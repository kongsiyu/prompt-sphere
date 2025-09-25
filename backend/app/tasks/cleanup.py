"""后台清理任务

提供会话清理、缓存清理、日志清理等后台维护任务
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.services.session import get_session_service
from database.repositories.audit_log_repository import AuditLogRepository
from database.session import get_session

logger = logging.getLogger(__name__)


class CleanupTasks:
    """后台清理任务类

    负责定期执行各种维护和清理任务
    """

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

        # 清理任务配置
        self.session_cleanup_interval = 3600  # 1小时执行一次会话清理
        self.cache_cleanup_interval = 1800  # 30分钟执行一次缓存清理
        self.log_cleanup_interval = 86400  # 24小时执行一次日志清理
        self.activity_cleanup_interval = 21600  # 6小时执行一次活动数据清理

        # 数据保留策略
        self.expired_session_retention_hours = 24  # 过期会话保留24小时
        self.audit_log_retention_days = 90  # 审计日志保留90天
        self.user_activity_retention_days = 30  # 用户活动保留30天
        self.temp_data_retention_hours = 12  # 临时数据保留12小时

        # 任务状态跟踪
        self._running_tasks = set()
        self._task_statistics = {}

    async def start_cleanup_scheduler(self) -> None:
        """启动清理任务调度器"""
        try:
            self.logger.info("Starting cleanup task scheduler")

            # 创建异步任务
            tasks = [
                asyncio.create_task(self._schedule_session_cleanup()),
                asyncio.create_task(self._schedule_cache_cleanup()),
                asyncio.create_task(self._schedule_log_cleanup()),
                asyncio.create_task(self._schedule_activity_cleanup()),
            ]

            # 等待所有任务完成（通常不会完成，除非出错）
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Error in cleanup scheduler: {e}")
            raise

    async def _schedule_session_cleanup(self) -> None:
        """调度会话清理任务"""
        while True:
            try:
                await asyncio.sleep(self.session_cleanup_interval)
                await self.cleanup_sessions()
            except Exception as e:
                self.logger.error(f"Error in session cleanup scheduler: {e}")
                # 等待一段时间后重试
                await asyncio.sleep(300)  # 5分钟后重试

    async def _schedule_cache_cleanup(self) -> None:
        """调度缓存清理任务"""
        while True:
            try:
                await asyncio.sleep(self.cache_cleanup_interval)
                await self.cleanup_cache()
            except Exception as e:
                self.logger.error(f"Error in cache cleanup scheduler: {e}")
                await asyncio.sleep(300)

    async def _schedule_log_cleanup(self) -> None:
        """调度日志清理任务"""
        while True:
            try:
                await asyncio.sleep(self.log_cleanup_interval)
                await self.cleanup_logs()
            except Exception as e:
                self.logger.error(f"Error in log cleanup scheduler: {e}")
                await asyncio.sleep(3600)  # 1小时后重试

    async def _schedule_activity_cleanup(self) -> None:
        """调度活动数据清理任务"""
        while True:
            try:
                await asyncio.sleep(self.activity_cleanup_interval)
                await self.cleanup_user_activities()
            except Exception as e:
                self.logger.error(f"Error in activity cleanup scheduler: {e}")
                await asyncio.sleep(1800)  # 30分钟后重试

    async def cleanup_sessions(self) -> Dict[str, Any]:
        """清理过期会话

        Returns:
            清理结果统计
        """
        task_name = "cleanup_sessions"
        if task_name in self._running_tasks:
            self.logger.info(f"Task {task_name} is already running, skipping")
            return {"status": "skipped", "reason": "already_running"}

        try:
            self._running_tasks.add(task_name)
            self.logger.info("Starting session cleanup task")

            session_service = get_session_service()
            result = await session_service.cleanup_expired_sessions()

            # 清理RefreshToken映射中的过期条目
            redis = await get_redis_client()
            expired_refresh_tokens = 0

            cursor = 0
            while True:
                cursor, keys = await redis.redis.scan(cursor, match="refresh_token:*", count=100)

                for key_bytes in keys:
                    key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                    ttl = await redis.ttl(key)
                    if ttl <= 0:  # 已过期
                        await redis.delete(key)
                        expired_refresh_tokens += 1

                if cursor == 0:
                    break

            result["expired_refresh_tokens"] = expired_refresh_tokens

            # 更新统计信息
            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "status": "success"
            }

            self.logger.info(f"Session cleanup completed: {result}")
            return result

        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": error_result,
                "status": "error"
            }
            self.logger.error(f"Session cleanup failed: {e}")
            return error_result

        finally:
            self._running_tasks.discard(task_name)

    async def cleanup_cache(self) -> Dict[str, Any]:
        """清理过期缓存数据

        Returns:
            清理结果统计
        """
        task_name = "cleanup_cache"
        if task_name in self._running_tasks:
            return {"status": "skipped", "reason": "already_running"}

        try:
            self._running_tasks.add(task_name)
            self.logger.info("Starting cache cleanup task")

            redis = await get_redis_client()
            cleaned_keys = 0
            total_scanned = 0

            # 清理用户相关缓存（过期的用户信息）
            cursor = 0
            while True:
                cursor, keys = await redis.redis.scan(cursor, match="user:*", count=100)
                total_scanned += len(keys)

                for key_bytes in keys:
                    key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                    ttl = await redis.ttl(key)

                    # 删除已过期或没有TTL的旧缓存
                    if ttl <= 0:
                        await redis.delete(key)
                        cleaned_keys += 1

                if cursor == 0:
                    break

            # 清理服务缓存
            service_cache_patterns = ["service:*", "health_check:*", "stats:*"]
            for pattern in service_cache_patterns:
                cursor = 0
                while True:
                    cursor, keys = await redis.redis.scan(cursor, match=pattern, count=100)
                    total_scanned += len(keys)

                    for key_bytes in keys:
                        key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                        ttl = await redis.ttl(key)

                        if ttl <= 0:
                            await redis.delete(key)
                            cleaned_keys += 1

                    if cursor == 0:
                        break

            result = {
                "cleaned_keys": cleaned_keys,
                "total_scanned": total_scanned,
                "cleanup_time": datetime.now(timezone.utc).isoformat()
            }

            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "status": "success"
            }

            self.logger.info(f"Cache cleanup completed: {result}")
            return result

        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": error_result,
                "status": "error"
            }
            self.logger.error(f"Cache cleanup failed: {e}")
            return error_result

        finally:
            self._running_tasks.discard(task_name)

    async def cleanup_logs(self) -> Dict[str, Any]:
        """清理过期日志数据

        Returns:
            清理结果统计
        """
        task_name = "cleanup_logs"
        if task_name in self._running_tasks:
            return {"status": "skipped", "reason": "already_running"}

        try:
            self._running_tasks.add(task_name)
            self.logger.info("Starting log cleanup task")

            # 计算删除阈值时间
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.audit_log_retention_days)

            deleted_logs = 0

            # 清理审计日志
            async with get_session() as session:
                audit_repo = AuditLogRepository(session.session)

                # 删除过期的审计日志
                try:
                    # 这里应该调用仓库的清理方法，但由于当前的审计日志仓库可能没有这个方法
                    # 我们直接使用SQL执行删除
                    from sqlalchemy import text
                    result = await session.session.execute(
                        text("DELETE FROM audit_logs WHERE created_at < :cutoff_date"),
                        {"cutoff_date": cutoff_date}
                    )
                    deleted_logs = result.rowcount
                    await session.session.commit()

                except Exception as e:
                    self.logger.warning(f"Error cleaning audit logs: {e}")
                    deleted_logs = 0

            result = {
                "deleted_audit_logs": deleted_logs,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": self.audit_log_retention_days,
                "cleanup_time": datetime.now(timezone.utc).isoformat()
            }

            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "status": "success"
            }

            self.logger.info(f"Log cleanup completed: {result}")
            return result

        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": error_result,
                "status": "error"
            }
            self.logger.error(f"Log cleanup failed: {e}")
            return error_result

        finally:
            self._running_tasks.discard(task_name)

    async def cleanup_user_activities(self) -> Dict[str, Any]:
        """清理过期用户活动数据

        Returns:
            清理结果统计
        """
        task_name = "cleanup_user_activities"
        if task_name in self._running_tasks:
            return {"status": "skipped", "reason": "already_running"}

        try:
            self._running_tasks.add(task_name)
            self.logger.info("Starting user activity cleanup task")

            redis = await get_redis_client()
            cleaned_activities = 0
            cleaned_counters = 0

            # 计算清理阈值日期
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.user_activity_retention_days)
            cutoff_timestamp = cutoff_date.timestamp()

            # 清理用户活动记录
            cursor = 0
            while True:
                cursor, keys = await redis.redis.scan(cursor, match="user_activity:*", count=100)

                for key_bytes in keys:
                    key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                    try:
                        activity_data_json = await redis.get(key)
                        if activity_data_json:
                            activity_data = json.loads(activity_data_json.decode())
                            activity_time = datetime.fromisoformat(
                                activity_data.get("timestamp", "")
                            ).timestamp()

                            if activity_time < cutoff_timestamp:
                                await redis.delete(key)
                                cleaned_activities += 1
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # 无效的数据，直接删除
                        await redis.delete(key)
                        cleaned_activities += 1

                if cursor == 0:
                    break

            # 清理用户活动计数器
            cursor = 0
            while True:
                cursor, keys = await redis.redis.scan(cursor, match="user_activity_count:*", count=100)

                for key_bytes in keys:
                    key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                    try:
                        # 从键名中提取日期
                        parts = key.split(":")
                        if len(parts) >= 3:
                            date_str = parts[2]
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                            if date_obj.timestamp() < cutoff_timestamp:
                                await redis.delete(key)
                                cleaned_counters += 1
                    except (ValueError, IndexError):
                        # 无效的键格式，跳过
                        continue

                if cursor == 0:
                    break

            # 清理临时数据
            temp_data_cleaned = await self._cleanup_temp_data()

            result = {
                "cleaned_activities": cleaned_activities,
                "cleaned_counters": cleaned_counters,
                "temp_data_cleaned": temp_data_cleaned,
                "retention_days": self.user_activity_retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "cleanup_time": datetime.now(timezone.utc).isoformat()
            }

            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "status": "success"
            }

            self.logger.info(f"User activity cleanup completed: {result}")
            return result

        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            self._task_statistics[task_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": error_result,
                "status": "error"
            }
            self.logger.error(f"User activity cleanup failed: {e}")
            return error_result

        finally:
            self._running_tasks.discard(task_name)

    async def _cleanup_temp_data(self) -> int:
        """清理临时数据

        Returns:
            清理的条目数
        """
        try:
            redis = await get_redis_client()
            cleaned_count = 0

            # 临时数据模式
            temp_patterns = [
                "temp:*",
                "lock:*",
                "rate_limit:*",
                "verification:*"
            ]

            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.temp_data_retention_hours)

            for pattern in temp_patterns:
                cursor = 0
                while True:
                    cursor, keys = await redis.redis.scan(cursor, match=pattern, count=100)

                    for key_bytes in keys:
                        key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                        ttl = await redis.ttl(key)

                        # 删除已过期或存在时间过长的键
                        if ttl <= 0:
                            await redis.delete(key)
                            cleaned_count += 1

                    if cursor == 0:
                        break

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Error cleaning temp data: {e}")
            return 0

    async def run_all_cleanup_tasks(self) -> Dict[str, Any]:
        """立即执行所有清理任务

        Returns:
            所有任务的执行结果
        """
        self.logger.info("Running all cleanup tasks manually")

        results = {}

        try:
            # 并发执行所有清理任务
            tasks = [
                self.cleanup_sessions(),
                self.cleanup_cache(),
                self.cleanup_logs(),
                self.cleanup_user_activities()
            ]

            task_names = ["sessions", "cache", "logs", "user_activities"]

            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(task_results):
                task_name = task_names[i]
                if isinstance(result, Exception):
                    results[task_name] = {
                        "status": "error",
                        "error": str(result)
                    }
                else:
                    results[task_name] = result

            overall_result = {
                "status": "completed",
                "execution_time": datetime.now(timezone.utc).isoformat(),
                "tasks": results,
                "summary": {
                    "total_tasks": len(task_names),
                    "successful_tasks": sum(
                        1 for r in results.values()
                        if r.get("status") != "error"
                    ),
                    "failed_tasks": sum(
                        1 for r in results.values()
                        if r.get("status") == "error"
                    )
                }
            }

            self.logger.info(f"All cleanup tasks completed: {overall_result['summary']}")
            return overall_result

        except Exception as e:
            self.logger.error(f"Error running all cleanup tasks: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_time": datetime.now(timezone.utc).isoformat()
            }

    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务执行统计信息

        Returns:
            任务统计信息
        """
        try:
            current_time = datetime.now(timezone.utc)

            # 添加运行时状态
            runtime_info = {
                "current_time": current_time.isoformat(),
                "running_tasks": list(self._running_tasks),
                "total_registered_tasks": 4
            }

            # 计算任务健康状态
            task_health = {}
            for task_name, stats in self._task_statistics.items():
                last_run_str = stats.get("last_run")
                if last_run_str:
                    last_run = datetime.fromisoformat(last_run_str)
                    hours_since_run = (current_time - last_run).total_seconds() / 3600

                    # 根据任务类型判断健康状态
                    max_hours = {
                        "cleanup_sessions": 2,  # 会话清理应该每小时运行
                        "cleanup_cache": 1,     # 缓存清理应该每30分钟运行
                        "cleanup_logs": 25,     # 日志清理应该每24小时运行
                        "cleanup_user_activities": 7  # 活动清理应该每6小时运行
                    }

                    expected_max = max_hours.get(task_name, 24)
                    is_healthy = (
                        hours_since_run <= expected_max and
                        stats.get("status") == "success"
                    )

                    task_health[task_name] = {
                        "is_healthy": is_healthy,
                        "hours_since_run": round(hours_since_run, 2),
                        "expected_max_hours": expected_max,
                        "last_status": stats.get("status", "unknown")
                    }
                else:
                    task_health[task_name] = {
                        "is_healthy": False,
                        "hours_since_run": None,
                        "expected_max_hours": 24,
                        "last_status": "never_run"
                    }

            overall_health = all(
                task_info["is_healthy"]
                for task_info in task_health.values()
            )

            return {
                "overall_health": overall_health,
                "runtime_info": runtime_info,
                "task_statistics": self._task_statistics,
                "task_health": task_health
            }

        except Exception as e:
            self.logger.error(f"Error getting task statistics: {e}")
            return {
                "overall_health": False,
                "runtime_info": {
                    "current_time": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                },
                "task_statistics": self._task_statistics,
                "task_health": {}
            }

    async def stop_all_tasks(self) -> Dict[str, Any]:
        """停止所有运行中的任务

        Returns:
            停止结果
        """
        try:
            self.logger.info("Attempting to stop all running cleanup tasks")

            stopped_tasks = list(self._running_tasks)

            # 清空运行任务集合
            self._running_tasks.clear()

            return {
                "status": "stopped",
                "stopped_tasks": stopped_tasks,
                "stop_time": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error stopping tasks: {e}")
            return {
                "status": "error",
                "error": str(e),
                "stop_time": datetime.now(timezone.utc).isoformat()
            }


# 全局清理任务实例
_cleanup_tasks: Optional[CleanupTasks] = None


def get_cleanup_tasks() -> CleanupTasks:
    """获取清理任务实例（单例模式）"""
    global _cleanup_tasks
    if _cleanup_tasks is None:
        _cleanup_tasks = CleanupTasks()
    return _cleanup_tasks


# 便捷函数
async def start_background_cleanup():
    """启动后台清理任务"""
    cleanup_tasks = get_cleanup_tasks()
    await cleanup_tasks.start_cleanup_scheduler()


async def run_cleanup_now():
    """立即运行所有清理任务"""
    cleanup_tasks = get_cleanup_tasks()
    return await cleanup_tasks.run_all_cleanup_tasks()


async def get_cleanup_status():
    """获取清理任务状态"""
    cleanup_tasks = get_cleanup_tasks()
    return await cleanup_tasks.get_task_statistics()