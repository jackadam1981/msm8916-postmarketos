#!/usr/bin/env python3
"""
check_version.py - postmarketOS 版本检查脚本

功能：
1. 查询 postmarketOS 最新 release 版本
2. 对比当前 version.txt 版本
3. 判断是否需要构建
4. 输出版本信息

用法:
    python scripts/check_version.py           # 检查并输出结果
    python scripts/check_version.py auto     # 强制自动模式
    python scripts/check_version.py 23.02    # 指定当前版本
"""

import urllib.request
import sys
import os
from pathlib import Path

# 项目路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(PROJECT_ROOT, "version.txt")


def get_latest_pmos_version():
    """查询 postmarketOS 最新 release 的版本"""
    try:
        resp = requests.get(
            "https://api.github.com/repos/postmarketOS/postmarketOS/releases/latest",
            headers={"Accept": "application/vnd.github+json"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        # tag_name 形如 "v23.02", 需要去掉前导的 "v"
        latest = data["tag_name"].lstrip("v")
        return latest
    except Exception as e:
        print(f"⚠️ 无法查询 postmarketOS latest release: {e}")
        return None


def read_current_version():
    """读取 version.txt 中的当前版本"""
    try:
        with open(VERSION_FILE, "r") as f:
            version = f.read().strip()
            # 如果是 "auto"，返回 None 表示需要特殊处理
            if version.lower() == "auto":
                return "auto"
            return version
    except FileNotFoundError:
        return None


def needs_build(current_version: str = None) -> bool:
    """
    判断是否需要构建
    
    逻辑：
    - 如果 current_version 为 "auto" 或 None：始终返回 True (需要构建)
    - 如果 current_version < latest release：返回 True (需要构建)
    - 否则返回 False (已经是最新版本，无需构建)
    """
    # 自动模式：始终构建
    if current_version == "auto" or current_version is None:
        latest = get_latest_pmos_version()
        # 即使是 auto 模式，也查询 latest 以便输出信息
        latest_version = latest or "unknown"
        print(f"🔍 自动模式: 检测到 latest postmarketOS version: {latest_version}")
        return True
    
    # 指定版本模式：进行版本比较
    latest = get_latest_pmos_version()
    if latest is None:
        # 查询失败，保险起见：需要构建
        print(f"⚠️ 无法查询 latest version，保险起见: 需要构建当前版本 {current_version}")
        return True
    
    # 版本比较
    # PMOS version 格式如 "23.02", "24.01" 等
    # 使用字符串比较，适用于这种格式
    if current_version < latest:
        print(f"🔨 需要构建: 当前版本 {current_version} < 最新版本 {latest}")
        return True
    else:
        print(f"✅ 已是最新版本: 当前版本 {current_version} >= 最新版本 {latest}")
        return False


def main():
    """主程序入口"""
    # 获取参数：版本号
    # 参数优先级: 命令行参数 > version.txt > auto
    arg_version = None
    if len(sys.argv) > 1:
        arg_version = sys.argv[1]
    
    # 获取 version.txt 中的当前版本
    current_version = read_current_version()
    
    # 如果命令行参数提供，优先使用命令行参数
    # 否则使用 version.txt 中的版本
    # 如果两者都没有，使用 "auto"
    if arg_version:
        current_version = arg_version
    
    # 判断是否需要构建
    needs_b = needs_build(current_version)
    
    # 输出版本信息摘要
    print("=" * 50)
    print("postmarketOS 版本检查结果")
    print("=" * 50)
    print()
    
    current_ver = arg_version if arg_version else (
        read_current_version() or "未设定"
    )
    latest_ver = get_latest_pmos_version() or "未知"
    
    print(f"当前版本: {current_ver}")
    print(f"最新版本: {latest_ver}")
    print()
    
    if needs_b:
        print("结论: 🔨 需要构建新的 boot.img")
    else:
        print("结论: ✅ 已是最新版本，无需构建")
    
    print()
    print("=" * 50)
    
    # 返回退出码
    # 0: 需要构建, 1: 不需要构建
    sys.exit(0 if needs_b else 1)


if __name__ == "__main__":
    main()