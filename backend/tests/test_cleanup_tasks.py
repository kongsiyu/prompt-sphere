"""清理任务测试

测试后台清理任务的所有功能
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.tasks.cleanup import CleanupTasks, get_cleanup_tasks


@pytest.fixture
async def cleanup_tasks():
    """清理任务实例"""
    tasks = CleanupTasks()
    yield tasks


class TestCleanupTasksInitialization:
    """测试清理任务初始化"""

    def test_cleanup_tasks_init(self, cleanup_tasks):
        """测试清理任务初始化"""
        assert cleanup_tasks.session_cleanup_interval == 3600
        assert cleanup_tasks.cache_cleanup_interval == 1800
        assert cleanup_tasks.log_cleanup_interval == 86400
        assert cleanup_tasks.activity_cleanup_interval == 21600

        assert cleanup_tasks.expired_session_retention_hours == 24
        assert cleanup_tasks.audit_log_retention_days == 90
        assert cleanup_tasks.user_activity_retention_days == 30
        assert cleanup_tasks.temp_data_retention_hours == 12

        assert isinstance(cleanup_tasks._running_tasks, set)
        assert isinstance(cleanup_tasks._task_statistics, dict)


class TestSessionCleanup:
    """测试会话清理功能"""

    @patch('app.tasks.cleanup.get_session_service')
    @patch('app.tasks.cleanup.get_redis_client')
    async def test_cleanup_sessions_success(self, mock_redis_client, mock_session_service, cleanup_tasks):
        """测试成功清理会话"""
        # 设置会话服务模拟
        mock_session_svc = AsyncMock()
        mock_session_svc.cleanup_expired_sessions.return_value = {
            "cleaned_sessions": 5,
            "cleaned_refresh_tokens": 3
        }
        mock_session_service.return_value = mock_session_svc

        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis.redis.scan.return_value = (0, [b"refresh_token:1", b"refresh_token:2"])
        mock_redis.ttl.side_effect = [-1, -1]  # 模拟过期的令牌
        mock_redis_client.return_value = mock_redis

        # 执行测试
        result = await cleanup_tasks.cleanup_sessions()

        # 验证结果
        assert result is not None
        assert result["cleaned_sessions"] == 5
        assert result["expired_refresh_tokens"] == 2

        # 验证调用
        mock_session_svc.cleanup_expired_sessions.assert_called_once()
        mock_redis.redis.scan.assert_called()

    @patch('app.tasks.cleanup.get_session_service')
    async def test_cleanup_sessions_error(self, mock_session_service, cleanup_tasks):
        """测试会话清理出错"""
        # 设置会话服务抛出异常
        mock_session_svc = AsyncMock()
        mock_session_svc.cleanup_expired_sessions.side_effect = Exception("清理失败")
        mock_session_service.return_value = mock_session_svc

        # 执行测试
        result = await cleanup_tasks.cleanup_sessions()

        # 验证结果
        assert result["status"] == "error"
        assert "清理失败" in result["error"]

    async def test_cleanup_sessions_already_running(self, cleanup_tasks):
        """测试会话清理已在运行"""
        # 模拟任务已在运行
        cleanup_tasks._running_tasks.add("cleanup_sessions")

        # 执行测试
        result = await cleanup_tasks.cleanup_sessions()

        # 验证结果
        assert result["status"] == "skipped"
        assert result["reason"] == "already_running"


class TestCacheCleanup:
    """测试缓存清理功能"""

    @patch('app.tasks.cleanup.get_redis_client')
    async def test_cleanup_cache_success(self, mock_redis_client, cleanup_tasks):
        """测试成功清理缓存"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()

        # 模拟扫描结果
        scan_results = [
            # 第一次扫描用户缓存
            (0, [b"user:1", b"user:2"]),
            # 服务缓存扫描
            (0, [b"service:test", b"health_check:test"]),
            (0, [b"stats:test"])
        ]
        mock_redis.redis.scan.side_effect = scan_results

        # 模拟TTL检查 - 有些过期，有些没有
        mock_redis.ttl.side_effect = [-1, 100, -1, 200, -1]
        mock_redis_client.return_value = mock_redis

        # 执行测试
        result = await cleanup_tasks.cleanup_cache()

        # 验证结果
        assert result is not None
        assert "cleaned_keys" in result
        assert "total_scanned" in result
        assert result["cleaned_keys"] >= 0

        # 验证调用
        mock_redis.redis.scan.assert_called()
        mock_redis.delete.assert_called()

    @patch('app.tasks.cleanup.get_redis_client')
    async def test_cleanup_cache_error(self, mock_redis_client, cleanup_tasks):
        """测试缓存清理出错"""
        # 设置Redis客户端抛出异常
        mock_redis = AsyncMock()
        mock_redis.redis.scan.side_effect = Exception("Redis连接失败")
        mock_redis_client.return_value = mock_redis

        # 执行测试
        result = await cleanup_tasks.cleanup_cache()

        # 验证结果
        assert result["status"] == "error"
        assert "Redis连接失败" in result["error"]


class TestLogCleanup:
    """测试日志清理功能"""

    @patch('app.tasks.cleanup.get_session')
    async def test_cleanup_logs_success(self, mock_get_session, cleanup_tasks):
        """测试成功清理日志"""
        # 设置数据库会话模拟
        mock_session_wrapper = AsyncMock()
        mock_session = AsyncMock()
        mock_session_wrapper.session = mock_session
        mock_get_session.return_value.__aenter__.return_value = mock_session_wrapper
        mock_get_session.return_value.__aexit__.return_value = None

        # 模拟SQL执行结果
        mock_result = MagicMock()
        mock_result.rowcount = 10
        mock_session.execute.return_value = mock_result

        # 执行测试
        result = await cleanup_tasks.cleanup_logs()

        # 验证结果
        assert result is not None
        assert result["deleted_audit_logs"] == 10
        assert "cutoff_date" in result
        assert result["retention_days"] == cleanup_tasks.audit_log_retention_days

        # 验证调用
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('app.tasks.cleanup.get_session')
    async def test_cleanup_logs_error(self, mock_get_session, cleanup_tasks):
        """测试日志清理出错"""
        # 设置数据库会话抛出异常
        mock_get_session.side_effect = Exception("数据库连接失败")

        # 执行测试
        result = await cleanup_tasks.cleanup_logs()

        # 验证结果
        assert result["status"] == "error"
        assert "数据库连接失败" in result["error"]


class TestUserActivityCleanup:
    """测试用户活动清理功能"""

    @patch('app.tasks.cleanup.get_redis_client')
    async def test_cleanup_user_activities_success(self, mock_redis_client, cleanup_tasks):
        """测试成功清理用户活动"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟活动数据
        old_activity_data = {
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(),
            "activity_type": "test",
            "user_id": "user1"
        }
        new_activity_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "activity_type": "test",
            "user_id": "user1"
        }

        # 模拟扫描结果
        mock_redis.redis.scan.side_effect = [
            # 扫描用户活动
            (0, [b"user_activity:old", b"user_activity:new"]),
            # 扫描活动计数器
            (0, [b"user_activity_count:user1:2024-01-01", b"user_activity_count:user1:2024-12-01"])
        ]

        # 模拟Redis get返回
        mock_redis.get.side_effect = [
            json.dumps(old_activity_data).encode(),
            json.dumps(new_activity_data).encode()
        ]

        # 模拟临时数据清理
        with patch.object(cleanup_tasks, '_cleanup_temp_data') as mock_cleanup_temp:
            mock_cleanup_temp.return_value = 5

            # 执行测试
            result = await cleanup_tasks.cleanup_user_activities()

            # 验证结果
            assert result is not None
            assert "cleaned_activities" in result
            assert "cleaned_counters" in result
            assert result["temp_data_cleaned"] == 5
            assert result["retention_days"] == cleanup_tasks.user_activity_retention_days

        # 验证调用
        mock_redis.redis.scan.assert_called()
        mock_redis.delete.assert_called()

    @patch('app.tasks.cleanup.get_redis_client')
    async def test_cleanup_temp_data(self, mock_redis_client, cleanup_tasks):
        """测试清理临时数据"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟扫描结果
        mock_redis.redis.scan.side_effect = [
            (0, [b"temp:1", b"temp:2"]),  # temp:*
            (0, [b"lock:1"]),             # lock:*
            (0, [b"rate_limit:1"]),       # rate_limit:*
            (0, [b"verification:1"])      # verification:*
        ]

        # 模拟TTL检查 - 有些过期
        mock_redis.ttl.side_effect = [-1, 100, -1, -1, -1]

        # 执行测试
        result = await cleanup_tasks._cleanup_temp_data()

        # 验证结果
        assert result >= 0

        # 验证调用
        mock_redis.redis.scan.assert_called()


class TestScheduledTasks:
    """测试定时任务调度"""

    @patch('asyncio.sleep')
    @patch.object(CleanupTasks, 'cleanup_sessions')
    async def test_schedule_session_cleanup(self, mock_cleanup_sessions, mock_sleep, cleanup_tasks):
        """测试会话清理调度"""
        # 模拟清理成功
        mock_cleanup_sessions.return_value = {"cleaned_sessions": 1}

        # 模拟sleep只执行一次后抛出异常来终止循环
        mock_sleep.side_effect = [None, Exception("Test stop")]

        # 执行测试（应该会因为异常而结束）
        try:
            await cleanup_tasks._schedule_session_cleanup()
        except Exception as e:
            assert str(e) == "Test stop"

        # 验证调用
        mock_cleanup_sessions.assert_called_once()
        mock_sleep.assert_called()

    @patch('asyncio.sleep')
    @patch.object(CleanupTasks, 'cleanup_cache')
    async def test_schedule_cache_cleanup_with_error(self, mock_cleanup_cache, mock_sleep, cleanup_tasks):
        """测试缓存清理调度遇到错误"""
        # 模拟清理失败
        mock_cleanup_cache.side_effect = Exception("清理失败")

        # 模拟sleep，第二次sleep时抛出异常终止循环
        mock_sleep.side_effect = [None, Exception("Test stop")]

        # 执行测试
        try:
            await cleanup_tasks._schedule_cache_cleanup()
        except Exception as e:
            assert str(e) == "Test stop"

        # 验证重试逻辑
        mock_cleanup_cache.assert_called_once()
        assert mock_sleep.call_count >= 1


class TestAllCleanupTasks:
    """测试所有清理任务"""

    @patch.object(CleanupTasks, 'cleanup_sessions')
    @patch.object(CleanupTasks, 'cleanup_cache')
    @patch.object(CleanupTasks, 'cleanup_logs')
    @patch.object(CleanupTasks, 'cleanup_user_activities')
    async def test_run_all_cleanup_tasks_success(
        self,
        mock_cleanup_activities,
        mock_cleanup_logs,
        mock_cleanup_cache,
        mock_cleanup_sessions,
        cleanup_tasks
    ):
        """测试成功运行所有清理任务"""
        # 设置所有清理任务返回成功
        mock_cleanup_sessions.return_value = {"cleaned_sessions": 5}
        mock_cleanup_cache.return_value = {"cleaned_keys": 10}
        mock_cleanup_logs.return_value = {"deleted_audit_logs": 20}
        mock_cleanup_activities.return_value = {"cleaned_activities": 15}

        # 执行测试
        result = await cleanup_tasks.run_all_cleanup_tasks()

        # 验证结果
        assert result is not None
        assert result["status"] == "completed"
        assert "tasks" in result
        assert "summary" in result

        assert result["summary"]["total_tasks"] == 4
        assert result["summary"]["successful_tasks"] == 4
        assert result["summary"]["failed_tasks"] == 0

        # 验证所有任务都被调用
        mock_cleanup_sessions.assert_called_once()
        mock_cleanup_cache.assert_called_once()
        mock_cleanup_logs.assert_called_once()
        mock_cleanup_activities.assert_called_once()

    @patch.object(CleanupTasks, 'cleanup_sessions')
    @patch.object(CleanupTasks, 'cleanup_cache')
    @patch.object(CleanupTasks, 'cleanup_logs')
    @patch.object(CleanupTasks, 'cleanup_user_activities')
    async def test_run_all_cleanup_tasks_with_errors(
        self,
        mock_cleanup_activities,
        mock_cleanup_logs,
        mock_cleanup_cache,
        mock_cleanup_sessions,
        cleanup_tasks
    ):
        """测试运行所有清理任务时部分失败"""
        # 设置部分任务失败
        mock_cleanup_sessions.return_value = {"cleaned_sessions": 5}
        mock_cleanup_cache.side_effect = Exception("缓存清理失败")
        mock_cleanup_logs.return_value = {"deleted_audit_logs": 20}
        mock_cleanup_activities.side_effect = Exception("活动清理失败")

        # 执行测试
        result = await cleanup_tasks.run_all_cleanup_tasks()

        # 验证结果
        assert result is not None
        assert result["status"] == "completed"
        assert result["summary"]["successful_tasks"] == 2
        assert result["summary"]["failed_tasks"] == 2

        # 验证错误任务
        assert result["tasks"]["cache"]["status"] == "error"
        assert result["tasks"]["user_activities"]["status"] == "error"


class TestTaskStatistics:
    """测试任务统计功能"""

    async def test_get_task_statistics_empty(self, cleanup_tasks):
        """测试获取空的任务统计"""
        result = await cleanup_tasks.get_task_statistics()

        assert result is not None
        assert "overall_health" in result
        assert "runtime_info" in result
        assert "task_statistics" in result
        assert "task_health" in result

        assert result["overall_health"] is False  # 因为没有任务运行过
        assert result["runtime_info"]["running_tasks"] == []

    async def test_get_task_statistics_with_data(self, cleanup_tasks):
        """测试获取有数据的任务统计"""
        # 模拟一些任务统计数据
        cleanup_tasks._task_statistics = {
            "cleanup_sessions": {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "result": {"cleaned_sessions": 5},
                "status": "success"
            },
            "cleanup_cache": {
                "last_run": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "result": {"status": "error", "error": "测试错误"},
                "status": "error"
            }
        }

        result = await cleanup_tasks.get_task_statistics()

        assert result is not None
        assert len(result["task_statistics"]) == 2
        assert len(result["task_health"]) >= 2

        # 验证健康状态计算
        sessions_health = result["task_health"]["cleanup_sessions"]
        assert sessions_health["is_healthy"] is True
        assert sessions_health["last_status"] == "success"

        cache_health = result["task_health"]["cleanup_cache"]
        assert cache_health["is_healthy"] is False
        assert cache_health["last_status"] == "error"

    async def test_get_task_statistics_error(self, cleanup_tasks):
        """测试获取任务统计时出错"""
        # 模拟datetime调用失败
        with patch('app.tasks.cleanup.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("时间获取失败")

            result = await cleanup_tasks.get_task_statistics()

            assert result["overall_health"] is False
            assert "error" in result["runtime_info"]


class TestTaskControl:
    """测试任务控制功能"""

    async def test_stop_all_tasks(self, cleanup_tasks):
        """测试停止所有任务"""
        # 模拟有运行中的任务
        cleanup_tasks._running_tasks.add("cleanup_sessions")
        cleanup_tasks._running_tasks.add("cleanup_cache")

        result = await cleanup_tasks.stop_all_tasks()

        assert result is not None
        assert result["status"] == "stopped"
        assert len(result["stopped_tasks"]) == 2
        assert "cleanup_sessions" in result["stopped_tasks"]
        assert "cleanup_cache" in result["stopped_tasks"]

        # 验证任务集合已清空
        assert len(cleanup_tasks._running_tasks) == 0

    async def test_stop_all_tasks_error(self, cleanup_tasks):
        """测试停止任务时出错"""
        # 模拟清空任务集合失败
        with patch.object(cleanup_tasks._running_tasks, 'clear') as mock_clear:
            mock_clear.side_effect = Exception("清空失败")

            result = await cleanup_tasks.stop_all_tasks()

            assert result["status"] == "error"
            assert "清空失败" in result["error"]


class TestCleanupTasksSingleton:
    """测试清理任务单例模式"""

    def test_get_cleanup_tasks_singleton(self):
        """测试获取清理任务实例是单例"""
        tasks1 = get_cleanup_tasks()
        tasks2 = get_cleanup_tasks()

        assert tasks1 is tasks2
        assert isinstance(tasks1, CleanupTasks)


class TestCleanupHelperFunctions:
    """测试清理任务辅助函数"""

    @patch('app.tasks.cleanup.get_cleanup_tasks')
    async def test_run_cleanup_now(self, mock_get_cleanup_tasks):
        """测试立即运行清理任务函数"""
        from app.tasks.cleanup import run_cleanup_now

        # 设置模拟
        mock_cleanup_tasks = AsyncMock()
        mock_cleanup_tasks.run_all_cleanup_tasks.return_value = {"status": "completed"}
        mock_get_cleanup_tasks.return_value = mock_cleanup_tasks

        # 执行测试
        result = await run_cleanup_now()

        # 验证结果
        assert result["status"] == "completed"
        mock_cleanup_tasks.run_all_cleanup_tasks.assert_called_once()

    @patch('app.tasks.cleanup.get_cleanup_tasks')
    async def test_get_cleanup_status(self, mock_get_cleanup_tasks):
        """测试获取清理状态函数"""
        from app.tasks.cleanup import get_cleanup_status

        # 设置模拟
        mock_cleanup_tasks = AsyncMock()
        mock_cleanup_tasks.get_task_statistics.return_value = {"overall_health": True}
        mock_get_cleanup_tasks.return_value = mock_cleanup_tasks

        # 执行测试
        result = await get_cleanup_status()

        # 验证结果
        assert result["overall_health"] is True
        mock_cleanup_tasks.get_task_statistics.assert_called_once()

    @patch('app.tasks.cleanup.get_cleanup_tasks')
    async def test_start_background_cleanup(self, mock_get_cleanup_tasks):
        """测试启动后台清理函数"""
        from app.tasks.cleanup import start_background_cleanup

        # 设置模拟
        mock_cleanup_tasks = AsyncMock()
        mock_cleanup_tasks.start_cleanup_scheduler.return_value = None
        mock_get_cleanup_tasks.return_value = mock_cleanup_tasks

        # 执行测试
        await start_background_cleanup()

        # 验证调用
        mock_cleanup_tasks.start_cleanup_scheduler.assert_called_once()


class TestCleanupTasksIntegration:
    """测试清理任务集成功能"""

    async def test_task_running_state_management(self, cleanup_tasks):
        """测试任务运行状态管理"""
        task_name = "cleanup_sessions"

        # 初始状态
        assert task_name not in cleanup_tasks._running_tasks

        # 模拟任务开始
        cleanup_tasks._running_tasks.add(task_name)
        assert task_name in cleanup_tasks._running_tasks

        # 模拟任务结束
        cleanup_tasks._running_tasks.discard(task_name)
        assert task_name not in cleanup_tasks._running_tasks

    async def test_task_statistics_update(self, cleanup_tasks):
        """测试任务统计更新"""
        task_name = "test_task"
        result = {"status": "success", "processed": 10}

        # 更新统计
        cleanup_tasks._task_statistics[task_name] = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "status": "success"
        }

        # 验证统计数据
        stats = cleanup_tasks._task_statistics[task_name]
        assert stats["status"] == "success"
        assert stats["result"]["processed"] == 10
        assert "last_run" in stats