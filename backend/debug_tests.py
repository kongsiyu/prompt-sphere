#!/usr/bin/env python3
"""
调试测试脚本 - 逐个运行测试方法找出卡死的测试
"""

import sys
import os
import subprocess
import signal
import time

if os.name == 'nt':
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 所有测试方法列表
test_methods = [
    # TestBaseAgentBasics
    "TestBaseAgentBasics::test_agent_initialization",
    "TestBaseAgentBasics::test_agent_capabilities",
    "TestBaseAgentBasics::test_send_message",
    "TestBaseAgentBasics::test_queue_full_handling",

    # TestBaseAgentLifecycle
    "TestBaseAgentLifecycle::test_start_stop_lifecycle",
    "TestBaseAgentLifecycle::test_restart",
    "TestBaseAgentLifecycle::test_duplicate_start_prevention",

    # TestBaseAgentMessageHandling
    "TestBaseAgentMessageHandling::test_task_message_processing",
    "TestBaseAgentMessageHandling::test_task_failure_handling",
    "TestBaseAgentMessageHandling::test_expired_task_handling",
    "TestBaseAgentMessageHandling::test_health_check_handling",
    "TestBaseAgentMessageHandling::test_status_message_handling",
    "TestBaseAgentMessageHandling::test_error_message_handling",

    # TestBaseAgentStatus
    "TestBaseAgentStatus::test_get_status",
    "TestBaseAgentStatus::test_load_percentage_calculation",
    "TestBaseAgentStatus::test_uptime_calculation",

    # TestBaseAgentHealthCheck
    "TestBaseAgentHealthCheck::test_health_check_success",
    "TestBaseAgentHealthCheck::test_dashscope_health_check",
    "TestBaseAgentHealthCheck::test_redis_health_check",

    # TestBaseAgentConcurrency
    "TestBaseAgentConcurrency::test_concurrent_task_processing",
    "TestBaseAgentConcurrency::test_max_concurrent_tasks_limit",

    # TestBaseAgentIntegration
    "TestBaseAgentIntegration::test_full_message_processing_workflow",
    "TestBaseAgentIntegration::test_error_recovery"
]

def run_single_test(test_method, timeout_seconds=15):
    """运行单个测试方法"""
    print(f"\n{'='*60}")
    print(f"🔍 测试: {test_method}")
    print(f"{'='*60}")

    cmd = [
        sys.executable, "-m", "pytest",
        f"app/tests/agents/test_base_agent.py::{test_method}",
        "-v", "--tb=short", "-s"
    ]

    start_time = time.time()
    try:
        # 使用 Popen 以便可以控制超时
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            elapsed_time = time.time() - start_time

            if process.returncode == 0:
                print(f"✅ PASSED ({elapsed_time:.2f}s)")
                return True, elapsed_time, None
            else:
                print(f"❌ FAILED ({elapsed_time:.2f}s)")
                print("STDOUT:", stdout[-500:] if stdout else "None")
                print("STDERR:", stderr[-500:] if stderr else "None")
                return False, elapsed_time, f"Exit code: {process.returncode}"

        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            print(f"⏱️ TIMEOUT after {elapsed_time:.2f}s - 强制终止进程")

            # 强制终止进程
            process.kill()
            try:
                stdout, stderr = process.communicate(timeout=2)
            except:
                stdout, stderr = "", ""

            print("STDOUT (before timeout):", stdout[-300:] if stdout else "None")
            print("STDERR (before timeout):", stderr[-300:] if stderr else "None")
            return False, elapsed_time, "TIMEOUT - 可能存在无限循环或死锁"

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"💥 ERROR ({elapsed_time:.2f}s): {e}")
        return False, elapsed_time, str(e)

def main():
    print("🚀 开始调试测试 - 逐个运行每个测试方法")
    print(f"总共 {len(test_methods)} 个测试方法")

    results = {}
    problem_tests = []

    for i, test_method in enumerate(test_methods, 1):
        print(f"\n[{i}/{len(test_methods)}] ", end="")

        success, elapsed_time, error_info = run_single_test(test_method)

        results[test_method] = {
            'success': success,
            'time': elapsed_time,
            'error': error_info
        }

        if not success:
            problem_tests.append(test_method)

        # 如果连续失败过多，询问是否继续
        if len(problem_tests) >= 3 and i < len(test_methods):
            print(f"\n⚠️  已经有 {len(problem_tests)} 个测试失败/超时")
            print("继续测试剩余的方法可能需要较长时间...")
            # response = input("是否继续？(y/n): ").lower().strip()
            # if response != 'y':
            #     print("用户选择停止测试")
            #     break

    # 生成报告
    print(f"\n{'='*80}")
    print("🔍 测试结果分析报告")
    print(f"{'='*80}")

    passed_tests = [name for name, result in results.items() if result['success']]
    failed_tests = [name for name, result in results.items() if not result['success']]
    timeout_tests = [name for name, result in results.items() if 'TIMEOUT' in str(result['error'])]

    print(f"\n📊 总体统计:")
    print(f"  ✅ 通过: {len(passed_tests)}/{len(results)}")
    print(f"  ❌ 失败: {len(failed_tests)}")
    print(f"  ⏱️  超时: {len(timeout_tests)}")

    if timeout_tests:
        print(f"\n🔥 超时的测试 (可能卡死):")
        for test in timeout_tests:
            error_info = results[test]['error']
            print(f"  - {test}")
            print(f"    {error_info}")

    if failed_tests and not timeout_tests:
        print(f"\n❌ 失败的测试:")
        for test in failed_tests:
            error_info = results[test]['error']
            print(f"  - {test}: {error_info}")

    # 性能分析
    if passed_tests:
        times = [results[test]['time'] for test in passed_tests]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        slow_tests = [test for test in passed_tests if results[test]['time'] > avg_time * 2]

        print(f"\n⚡ 性能分析:")
        print(f"  平均用时: {avg_time:.2f}s")
        print(f"  最长用时: {max_time:.2f}s")
        if slow_tests:
            print(f"  较慢的测试:")
            for test in slow_tests:
                print(f"    - {test}: {results[test]['time']:.2f}s")

    # 问题诊断建议
    if timeout_tests:
        print(f"\n💡 问题诊断建议:")
        print("  超时测试通常由以下原因导致:")
        print("  1. 无限循环 (while True 没有正确的退出条件)")
        print("  2. 异步死锁 (await 等待永远不会完成的任务)")
        print("  3. 资源等待 (等待网络、文件IO等)")
        print("  4. 测试依赖没有正确清理")

        print(f"\n🔧 建议的解决步骤:")
        print("  1. 检查超时测试中的异步操作")
        print("  2. 确认所有 await 调用都有超时或退出条件")
        print("  3. 检查测试的setUp和tearDown是否正确")
        print("  4. 考虑添加更多的调试日志")

if __name__ == "__main__":
    main()