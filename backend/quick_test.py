#!/usr/bin/env python3
"""快速测试每个测试类"""

import sys
import os
import subprocess

if os.name == 'nt':
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 测试类列表
test_classes = [
    "TestBaseAgentBasics",
    "TestBaseAgentLifecycle",
    "TestBaseAgentMessageHandling",
    "TestBaseAgentStatus",
    "TestBaseAgentHealthCheck",
    "TestBaseAgentConcurrency",
    "TestBaseAgentIntegration"
]

def run_test_class(class_name):
    """运行单个测试类"""
    print(f"\n=== 测试 {class_name} ===")

    cmd = [
        sys.executable, "-m", "pytest",
        f"app/tests/agents/test_base_agent.py::{class_name}",
        "-v", "--tb=short", "--timeout=10"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=".")

        if result.returncode == 0:
            print(f"✅ {class_name} - PASSED")
            return True
        else:
            print(f"❌ {class_name} - FAILED")
            print("STDOUT:", result.stdout[-300:] if result.stdout else "None")
            print("STDERR:", result.stderr[-300:] if result.stderr else "None")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️ {class_name} - TIMEOUT (可能卡住)")
        return False
    except Exception as e:
        print(f"💥 {class_name} - ERROR: {e}")
        return False

def main():
    print("开始快速测试各个测试类...")

    results = {}
    for test_class in test_classes:
        results[test_class] = run_test_class(test_class)

    print("\n" + "="*50)
    print("测试结果汇总:")
    for test_class, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL/TIMEOUT"
        print(f"  {test_class}: {status}")

    failed_count = sum(1 for x in results.values() if not x)
    print(f"\n总计: {len(test_classes) - failed_count}/{len(test_classes)} 通过")

    if failed_count > 0:
        print(f"\n有 {failed_count} 个测试类失败或超时，建议逐个检查。")

if __name__ == "__main__":
    main()