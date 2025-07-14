"""
命令行接口模块

直接透传给官方 7zz 二进制文件，确保用户获得完整的官方 7-Zip 功能。
py7zz 的价值在于自动管理二进制文件和提供 Python API。
"""

import os
import subprocess
import sys

from .core import find_7z_binary


def main() -> None:
    """
    主入口点：直接透传所有参数给官方 7zz
    
    这样可以确保：
    1. 用户获得完整的官方 7zz 功能
    2. 不需要维护参数映射和功能同步
    3. py7zz 专注于 Python API 和二进制文件管理
    """
    try:
        # 获取 py7zz 管理的 7zz 二进制文件
        binary_path = find_7z_binary()
        
        # 直接透传所有命令行参数
        cmd = [binary_path] + sys.argv[1:]
        
        # 使用 exec 替换当前进程，确保信号处理等行为与原生 7zz 一致
        if os.name == 'nt':  # Windows
            # Windows 下使用 subprocess 并等待结果
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        else:  # Unix-like systems
            # Unix 下使用 execv 替换进程
            os.execv(binary_path, cmd)
            
    except Exception as e:
        print(f"py7zz error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()