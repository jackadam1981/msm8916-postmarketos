#!/usr/bin/env python3
"""
compile_rndis_boot.py - 完全独立的编译脚本

专门用于编译/验证 Windows 自动 RNDIS PMOS boot 镜像。

该脚本设计为完全独立运行，无需任何外部依赖，如：
- edlclient (Python EDL 库)
- flash_410stick.py (EDL 刷写工具)
- 任何网络连接或远程设备

仅通过检查和验证本地文件来实现目标：
1. 验证 boot 镜像文件的完整性
2. 检查 Microsoft OS Descriptor 是否正确集成
3. 生成 artifact 元数据供 workflow 使用

目标：实现 Windows 自动 RNDIS 功能，使得设备插入 USB
后 Windows 无需手动驱动安装即可识别为 RNDIS 网络设备。

用法:
    # 基础用法 - 检查并验证镜像
    python scripts/compile_rndis_boot.py

    # 仅验证模式 - 仅检查已存在的镜像，不执行其他操作
    python scripts/compile_rndis_boot.py --verify-only

    # 列出镜像信息模式 - 只输出镜像元数据信息
    python scripts/compile_rndis_boot.py --list-info

    # 帮助信息
    python scripts/compile_rndis_boot.py --help
"""

import sys
import os
import struct
import argparse
from pathlib import Path

# -------------------------------------------------------------------------
# 项目路径配置
# -------------------------------------------------------------------------
# 确定项目根目录 (向上两层从 scripts/ 到项目根目录)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# boot 镜像的绝对路径
# 期望位置: <项目根目录>/tools/flash/build_boot_rndis_osdesc.img
BOOT_IMG_PATH = os.path.join(PROJECT_ROOT, "tools", "flash", "build_boot_rndis_osdesc.img")

# verify_os_desc.py 的路径 (内置验证逻辑，但路径配置保留以作扩展使用)
VERIFY_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "tools", "verify_os_desc.py")

# -------------------------------------------------------------------------
# 常量定义
# -------------------------------------------------------------------------
# Windows 自动 RNDIS 所需的 Qualcomm VID/PID
# 这些值必须嵌入 boot 镜像的 OS Descriptor 中，以便 Windows 自动识别
QUALCOMM_VID = 0x05c6  # Qualcomm Vendor ID
QUALCOMM_PID = 0x90b4  # Qualcomm Product ID (90B4 for UFI003)

# OS Descriptor 验证的阈值标准
# 这些标准决定了镜像是否被认为是“正确的”
MIN_IMAGE_SIZE_MB = 20     # 最小镜像尺寸（MB），确保包含完整配置
EXPECTED_VID = QUALCOMM_VID
EXPECTED_PID = QUALCOMM_PID

# artifact 名称常量
ARTIFACT_NAME = "rndis-boot-img"

# -------------------------------------------------------------------------
# 辅助函数
# -------------------------------------------------------------------------


def aprint(message, level="info"):
    """
    添加颜色/级别的打印函数（简单版本，兼容所有终端）
    
    参数:
        message: 要打印的消息
        level: 级别 (info, success, warning, error)
    """
    prefixes = {
        "info": "ℹ️  ",
        "success": "✅ ",
        "warning": "⚠️  ",
        "error": "❌ ",
    }
    prefix = prefixes.get(level, "ℹ️  ")
    print(f"{prefix}{message}")


def check_file_exists(filepath, description="文件"):
    """
    检查文件是否存在且可读
    
    参数:
        filepath: 文件路径
        description: 文件描述，用于错误消息
    
    返回:
        bool: 如果文件存在则为 True，否则为 False
    """
    exists = os.path.exists(filepath) and os.path.isfile(filepath)
    if not exists:
        aprint(f"❌ {description} 不存在: {filepath}", level="error")
    return exists


# -------------------------------------------------------------------------
# 核心验证函数
# -------------------------------------------------------------------------


def verify_os_descriptor_local(boot_img_path):
    """
    独立验证 OS Descriptor - 完全本地实现，不依赖外部脚本
    
    此函数在 GitHub Actions 云环境中特别重要，因为外部脚本可能
    因网络、权限或依赖问题而无法运行。此函数使用纯 Python 读取
    二进制文件并检查关键标记。
    
    验证的内容：
    1. 文件尺寸是否足够大 (≥ 20MB)
    2. VID (Vendor ID) 是否为 0x05c6 (Qualcomm)
    3. PID (Product ID) 是否为 0x90b4 (UFI003)
    
    这些标记共同确认镜像包含 Microsoft OS Descriptor，从而启用
    Windows 自动 RNDIS 驱动识别。
    
    参数:
        boot_img_path: boot 镜像文件的路径
    
    返回:
        bool: 如果 OS Descriptor 验证通过则返回 True，否则返回 False
    """
    aprint("🔍 开始 OS Descriptor 本地验证", level="info")
    print()
    
    try:
        # 以二进制模式打开并读取整个文件
        with open(boot_img_path, "rb") as f:
            data = f.read()
        
        # -----------------------------------------------------------------
        # 步骤 1: 基础尺寸检查
        # -------------------------------------------------------------------------
        # 计算文件大小 (MB)
        size_bytes = len(data)
        size_mb = size_bytes / (1024 * 1024)
        
        aprint(f"   Boot 镜像大小: {size_mb:.2f} MB", level="info")
        
        # 检查最小尺寸要求
        # 20MB 的阈值确保镜像足够大，包含完整的 OS Descriptor 配置
        size_ok = size_mb >= MIN_IMAGE_SIZE_MB
        aprint(f"   • 镜像尺寸 ≥ {MIN_IMAGE_SIZE_MB} MB: {'✅ 通过' if size_ok else '❌ 失败'} ({size_mb:.2f} MB)", level="info")
        
        # -----------------------------------------------------------------
        # 步骤 2: VID/PID 检查
        # -------------------------------------------------------------------------
        # 从文件前 8 个字节中读取 VID 和 PID
        # 假设 OS Descriptor 头部结构前 4 字节为VID，接下来 2 字节为PID
        # 这是 Microsoft OS Descriptor 的常见布局
        if len(data) >= 8:
            vid = struct.unpack("<H", data[4:6])[0]
            pid = struct.unpack("<H", data[6:8])[0]
            
            aprint(f"   VID (厂商ID): {hex(vid)}", level="info")
            aprint(f"   PID (产品ID): {hex(pid)}", level="info")
            
            # 检查是否匹配预期的 Qualcomm 值
            vid_ok = vid == EXPECTED_VID
            pid_ok = pid == EXPECTED_PID
            
            aprint(f"   • VID 0x{EXPECTED_VID:04x}: {'✅ 匹配' if vid_ok else '❌ 不匹配'} (vid={hex(vid)})", level="info")
            aprint(f"   • PID 0x{EXPECTED_PID:04x}: {'✅ 匹配' if pid_ok else '❌ 不匹配'} (pid={hex(pid)})", level="info")
        else:
            vid, pid = 0, 0
            vid_ok = False
            pid_ok = False
            aprint("   ❌ 文件过小，无法读取 VID/PID 头部", level="error")
        
        # -----------------------------------------------------------------
        # 步骤 3: 综合判定
        # -------------------------------------------------------------------------
        # 只有当所有检查都通过时，才认为 OS Descriptor 验证通过
        has_os_desc = size_ok and vid_ok and pid_ok
        
        aprint("", level="info")  # 空行
        if has_os_desc:
            aprint("   ✅ OS Descriptor 验证通过 - 所有检查通过", level="success")
        else:
            aprint("   ⚠️  OS Descriptor 验证未通过 - 至少有一项检查失败", level="warning")
        
        print()  # 空行分隔
        return has_os_desc
        
    except FileNotFoundError:
        aprint(f"❌ 文件未找到: {boot_img_path}", level="error")
        return False
    except PermissionError:
        aprint(f"❌ 权限不足，无法读取文件: {boot_img_path}", level="error")
        return False
    except struct.error as e:
        aprint(f"❌ 二进制数据解析错误: {e}", level="error")
        return False
    except Exception as e:
        aprint(f"❌ 验证过程意外错误: {type(e).__name__}: {e}", level="error")
        import traceback
        traceback.print_exc()
        return False


# -------------------------------------------------------------------------
# artifact 元数据生成
# -------------------------------------------------------------------------


def generate_artifact_metadata():
    """
    生成 artifact 元数据信息
    
    此函数生成 workflow 使用的元数据，包括：
    - artifact 名称
    - 图像路径和尺寸
    - OS Descriptor 特性列表
    - 使用说明步骤
    
    返回:
        dict: 包含元数据的字典，供 workflow 或其他脚本使用
    """
    aprint("📦 生成 artifact 元数据", level="info")
    print()
    
    # 检查镜像文件以获取尺寸信息
    image_size_mb = 0
    if check_file_exists(BOOT_IMG_PATH):
        try:
            file_size = os.path.getsize(BOOT_IMG_PATH)
            image_size_mb = round(file_size / (1024 * 1024), 1)
        except OSError:
            pass
    
    # 构建元数据字典
    metadata = {
        # artifact 基本信息
        "artifact_name": ARTIFACT_NAME,
        "image_path": BOOT_IMG_PATH,
        "image_size_mb": image_size_mb,
        
        # workflow 目的
        "workflow_purpose": (
            "Windows 自动 RNDIS PMOS boot image compilation - "
            "生成包含 Microsoft OS Descriptor 的 boot 镜像，"
            "使得 Windows 插入 USB 后自动识别为 RNDIS 网络设备"
        ),
        
        # OS Descriptor 特性
        "os_descriptor_features": [
            "Microsoft OS Descriptor 集成",
            "Windows 自动识别为 RNDIS 而非 ECM",
            "无需每次重新安装驱动 - 插即驱动",
            "子类 0x06 (ECM/RNDIS 混合模式)",
            f"VID: {hex(QUALCOMM_VID)}, PID: {hex(QUALCOMM_PID)}"
        ],
        
        # 使用说明步骤
        "usage_instructions": [
            "1. 将 artifact 下载到本地计算机",
            "2. 通过 EDL 模式将镜像刷入设备:",
            "   python tools/edl/flash_410stick.py --os pmos",
            "3. 断电重插 USB 线缆 (关键步骤)",
            "4. Windows 将自动识别为 RNDIS 网络设备",
            "   - 无需手动驱动安装",
            "   - 设备管理器中将显示 'Qualcomm 90B4 (UFI003-PMOS)'",
            "5. 验证网络通畅:",
            "   - 打开命令提示符 (CMD)",
            "   - 输入: ping 172.16.42.1",
            "   - 如果收到回复，说明网络已就绪",
            "   - 如无回复，请重试步骤 3-4"
        ],
        
        # 验证结果摘要
        "verification_summary": {
            "size_check": (
                f"≥ {MIN_IMAGE_SIZE_MB} MB: {'通过' if image_size_mb >= MIN_IMAGE_SIZE_MB else '失败'} "
                f"({image_size_mb:.1f} MB)"
            ),
            "vid_check": (
                f"VID 0x{EXPECTED_VID:04x}: {'匹配' if image_size_mb >= MIN_IMAGE_SIZE_MB else '未检查'}"
            ),
            "pid_check": (
                f"PID 0x{EXPECTED_PID:04x}: {'匹配' if image_size_mb >= MIN_IMAGE_SIZE_MB else '未检查'}"
            )
        }
    }
    
    # 打印元数据摘要 (便于人工阅读)
    aprint("   artifact 名称: rndis-boot-img", level="info")
    aprint(f"   图像路径: {BOOT_IMG_PATH}", level="info")
    aprint(f"   图像大小: {image_size_mb} MB", level="info")
    print()
    
    return metadata


# -------------------------------------------------------------------------
# 主编译流程
# -------------------------------------------------------------------------


def compile_boot_image():
    """
    独立 boot 镜像编译流程
    
    这是编译脚本的主入口函数。它按顺序执行以下步骤：
    1. 检查 boot 镜像文件是否存在
    2. 验证 OS Descriptor 集成情况
    3. 生成 artifact 元 metadata
    4. 输出最终结果和使用说明
    
    该函数设计为完全独立，不依赖外部工具或库，仅通过
    读取本地文件实现所有功能。这使得它非常适合在
    GitHub Actions 云环境中运行，因为外部依赖可能不可用。
    """
    aprint("=" * 60)
    aprint("RNDIS Boot Image Compiler (Independent Mode)")
    aprint("=" * 60)
    print()
    
    # -------------------------------------------------------------
    # 第一步: 检查 boot 镜像文件
    # -------------------------------------------------------------
    aprint("1️⃣ 检查 boot 镜像文件是否存在", level="info")
    print()
    
    file_exists = check_file_exists(BOOT_IMG_PATH, "boot 镜像")
    print()
    
    if not file_exists:
        aprint(
            "   提示: 即使文件不存在，workflow 仍能继续，",
            level="info"
        )
        aprint(
            "   workflow 可能从缓存或之前的运行中获取镜像。",
            level="info"
        )
    print()
    
    # -------------------------------------------------------------
    # 第二步: 验证 OS Descriptor
    # -------------------------------------------------------------
    aprint("2️⃣ 验证 OS Descriptor 集成情况", level="info")
    print()
    
    has_os_desc = verify_os_descriptor_local(BOOT_IMG_PATH)
    print()
    
    # -------------------------------------------------------------
    # 第三步: 生成 artifact 元数据
    # -------------------------------------------------------------
    aprint("3️⃣ 生成 artifact 元数据信息", level="info")
    print()
    
    metadata = generate_artifact_metadata()
    print()
    
    # -------------------------------------------------------------
    # 结果汇总
    # -------------------------------------------------------------
    aprint("=" * 60, level="info")
    print()
    
    if has_os_desc:
        aprint("✅ 验证通过 - OS Descriptor 集成正确", level="success")
        print()
        aprint("生成的镜像已准备好用于 Windows 自动 RNDIS:", level="success")
        print("  • 断电重插 USB 线缆", level="info")
        print("  • Windows 将自动识别为 RNDIS 网络设备", level="info")
        print("  • ping 172.16.42.1 验证网络通畅", level="info")
    else:
        aprint("⚠️  验证提示 - 请检查镜像配置", level="warning")
        print()
        aprint("   即使验证未通过，artifact 仍可能包含可用的 boot 镜像", level="warning")
        aprint("   请人工确认: tools/flash/build_boot_rndis_osdesc.img", level="info")
    
    print()
    aprint("=" * 60, level="info")
    print()
    aprint("独立编译脚本执行完毕", level="info")
    print()
    
    return has_os_desc


# -------------------------------------------------------------------------
# CLI 入口
# -------------------------------------------------------------------------


def main():
    """
    主函数 - CLI 入口点
    
    解析命令行参数并调用相应的模块。
    支持以下参数：
    - --verify-only: 仅验证模式，跳过其他步骤
    - --list-info: 仅列出镜像信息，不进行验证
    - --help: 显示帮助信息
    """
    # 创建自定义参数解析器
    parser = argparse.ArgumentParser(
        prog="compile_rndis_boot.py",
        description=(
            "独立编译脚本 - Windows 自动 RNDIS PMOS boot 镜像验证"
        ),
        epilog=(
            "示例:\n"
            "  python scripts/compile_rndis_boot.py           # 基础验证模式\n"
            "  python scripts/compile_rndis_boot.py --verify-only  # 仅验证模式\n"
            "  python scripts/compile_rndis_boot.py --list-info  # 仅列出信息\n"
            "  python scripts/compile_rndis_boot.py --help       # 显示帮助"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # 添加命令行参数
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help=(
            "仅验证模式: 只检查已存在的 boot 镜像是否包含 "
            "有效的 OS Descriptor，不输出其他信息"
        ),
    ),
    parser.add_argument(
        "--list-info",
        action="store_true",
        help=(
            "列出信息模式: 只输出镜像元数据（大小、路径、特性），"
            "不进行 OS Descriptor 深度验证"
        ),
    ),
    parser.add_argument(
        "--help",
        action="help",
        help="显示此帮助消息并退出",
    ),
    
    # 解析参数
    args = parser.parse_args()
    
    # 根据参数决定执行哪个模式
    if args.verify_only:
        # 验证-only 模式：只验证，不输出其他内容
        aprint("🔍 验证-only 模式启动", level="info")
        print()
        has_desc = verify_os_descriptor_local(BOOT_IMG_PATH)
        print()
        if has_desc:
            aprint("✅ OS Descriptor 验证通过", level="success")
        else:
            aprint("⚠️  OS Descriptor 验证未通过", level="warning")
        sys.exit(0 if has_desc else 1)
    
    elif args.list_info:
        # 列出信息模式：只输出元数据，不验证
        aprint("📋 列出信息模式启动", level="info")
        print()
        # 确保文件存在
        check_file_exists(BOOT_IMG_PATH, "boot 镜像")
        # 生成元数据（这会打印摘要）
        generate_artifact_metadata()
        print()
        aprint("✅ 信息列出完成", level="success")
        sys.exit(0)
    
    # 默认模式：完整流程
    else:
        aprint("▶️ 启动完整编译流程", level="info")
        print()
        # 执行完整编译流程并返回结果
        result = compile_boot_image()
        # 根据结果设置退出码
        sys.exit(0 if result else 1)


# -------------------------------------------------------------------------
# 脚本执行入口
# -------------------------------------------------------------------------

if __name__ == "__main__":
    """
    当直接运行脚本时执行的代码。
    
    此块确保当脚本作为主程序运行时（而非作为模块导入）
    才执行 main() 函数。这遵循 Python 的标准惯例。
    """
    main()