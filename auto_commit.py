#!/usr/bin/env python3
"""
自动提交数据更新到GitHub
当数据更新后，自动提交并推送到GitHub仓库
"""
import os
import subprocess
from datetime import datetime

def run_command(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """主函数"""
    project_dir = '/root/stock-zt-web'
    os.chdir(project_dir)

    # 检查是否有更改
    success, stdout, _ = run_command('git status --porcelain')
    if not success:
        print("❌ Git status 检查失败")
        return False

    if not stdout.strip():
        print("✅ 没有需要提交的更改")
        return True

    # 添加所有更改
    success, stdout, stderr = run_command('git add .')
    if not success:
        print(f"❌ Git add 失败: {stderr}")
        return False

    # 提交更改
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_message = f"update: 数据库更新 {timestamp}"
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success:
        print(f"❌ Git commit 失败: {stderr}")
        return False

    print(f"✅ 提交成功: {commit_message}")

    # 推送到GitHub
    success, stdout, stderr = run_command('git push origin main')
    if not success:
        print(f"❌ Git push 失败: {stderr}")
        return False

    print(f"✅ 推送到GitHub成功: {timestamp}")
    return True

if __name__ == '__main__':
    print(f"[{datetime.now()}] 开始自动提交数据更新...")
    result = main()
    if result:
        print("✅ 数据更新已自动提交到GitHub")
    else:
        print("❌ 数据更新提交失败")
