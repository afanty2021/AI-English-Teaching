"""
PDF 辅助工具 - AI英语教学系统
提供跨平台中文字体检测和配置功能
"""
import logging
import platform
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def get_system_platform() -> str:
    """
    获取当前系统平台

    Returns:
        系统平台名称: 'Darwin' (macOS), 'Windows', 'Linux'
    """
    return platform.system()


def get_chinese_fonts() -> List[str]:
    """
    获取系统可用的中文字体族名称

    Returns:
        中文字体族名称列表，按优先级排序
    """
    system = get_system_platform()

    if system == "Darwin":  # macOS
        return [
            "PingFang SC",      # 苹方-简体中文 (推荐)
            "PingFang TC",      # 苹方-繁体中文
            "Heiti SC",         # 黑体-简体
            "STHeiti",          # 华文黑体
            "STSong",           # 华文宋体
            "STKaiti",          # 华文楷体
        ]
    elif system == "Windows":
        return [
            "Microsoft YaHei",  # 微软雅黑 (推荐)
            "SimHei",           # 黑体
            "SimSun",           # 宋体
            "KaiTi",            # 楷体
            "FangSong",         # 仿宋
        ]
    else:  # Linux 及其他
        return [
            "Noto Sans CJK SC",    # 思源黑体 (推荐)
            "Noto Sans CJK TC",    # 思源黑体繁体
            "WenQuanYi Micro Hei", # 文泉驿微米黑
            "WenQuanYi Zen Hei",   # 文泉驿正黑
            "Droid Sans Fallback", # Android 后备字体
            "AR PL UMing CN",      # 文鼎PL简中明
            "AR PL UKai CN",       # 文鼎PL简中楷
        ]


def get_font_paths() -> Dict[str, List[str]]:
    """
    获取系统中字体文件的搜索路径

    Returns:
        字体文件路径字典，按平台分类
    """
    return {
        "Darwin": [
            "/System/Library/Fonts",
            "/System/Library/Fonts/Supplemental",
            "/Library/Fonts",
            "~/Library/Fonts",
        ],
        "Windows": [
            "C:\\Windows\\Fonts",
            "%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts",
        ],
        "Linux": [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "~/.fonts",
            "~/.local/share/fonts",
        ],
    }


def check_font_availability() -> Dict[str, any]:
    """
    检查系统中可用的中文字体

    Returns:
        包含字体可用性信息的字典
    """
    system = get_system_platform()
    font_families = get_chinese_fonts()
    font_paths = get_font_paths()

    available_fonts = []
    missing_fonts = []

    # 检查字体文件是否存在
    search_paths = font_paths.get(system, [])

    # 扩展用户路径
    expanded_paths = []
    for path in search_paths:
        expanded = Path(path).expanduser()
        if expanded.exists():
            expanded_paths.append(expanded)

    # 常见中文字体文件名映射
    font_files = {
        "PingFang SC": ["PingFang.ttc", "PingFang SC.ttc"],
        "Microsoft YaHei": ["msyh.ttc", "msyh.ttf", "msyhbd.ttc"],
        "SimSun": ["simsun.ttc", "simsun.ttf"],
        "Noto Sans CJK SC": ["NotoSansCJK-Regular.ttc", "NotoSansCJK_SC.otf"],
        "WenQuanYi Micro Hei": ["wqy-microhei.ttc", "wqy-microhei.ttf"],
    }

    # 检查字体文件
    for font_name, file_names in font_files.items():
        found = False
        for base_path in expanded_paths:
            for file_name in file_names:
                font_path = base_path / file_name
                if font_path.exists():
                    available_fonts.append({
                        "name": font_name,
                        "file": str(font_path),
                    })
                    found = True
                    break
            if found:
                break
        if not found and font_name in font_families:
            missing_fonts.append(font_name)

    return {
        "system": system,
        "available_fonts": available_fonts,
        "missing_fonts": missing_fonts,
        "font_families": font_families,
        "search_paths": [str(p) for p in expanded_paths],
    }


def get_css_font_families() -> str:
    """
    获取 CSS font-family 声明字符串

    Returns:
        CSS font-family 字符串
    """
    fonts = get_chinese_fonts()
    # 添加通用的后备字体
    fonts.extend(["sans-serif", "Arial", "Helvetica"])
    return ", ".join(f'"{f}"' if " " in f else f for f in fonts)


def generate_font_css() -> str:
    """
    生成字体相关的 CSS

    Returns:
        CSS 样式字符串
    """
    font_family = get_css_font_families()

    return f"""
    /* 中文字体支持 - {get_system_platform()} */
    body {{
        font-family: {font_family};
    }}

    /* 代码字体 */
    code, pre {{
        font-family: "Consolas", "Monaco", "Courier New", monospace;
    }}
    """


def log_font_info() -> None:
    """记录字体信息到日志"""
    font_info = check_font_availability()

    logger.info(f"PDF Font Info for {font_info['system']}:")
    logger.info(f"  Available fonts: {[f['name'] for f in font_info['available_fonts']]}")

    if font_info['missing_fonts']:
        logger.warning(f"  Missing fonts: {font_info['missing_fonts']}")
        logger.warning("  Some Chinese characters may not display correctly.")

    logger.debug(f"  Search paths: {font_info['search_paths']}")


def install_weasyprint_system_fonts() -> Dict[str, str]:
    """
    检查并返回 weasyprint 需要的系统字体配置

    Returns:
        字体配置信息字典
    """
    font_info = check_font_availability()

    # 如果没有找到可用字体，给出安装建议
    if not font_info['available_fonts']:
        system = font_info['system']
        install_commands = {
            "Darwin": "macOS 通常自带中文字体，无需额外安装",
            "Windows": "Windows 系统自带中文字体，无需额外安装",
            "Linux": (
                "Ubuntu/Debian: sudo apt-get install fonts-noto-cjk "
                "fonts-wqy-microhei fonts-wqy-zenhei"
            ),
        }

        return {
            "status": "no_fonts_found",
            "system": system,
            "recommendation": install_commands.get(system, "请安装系统中文字体"),
        }

    return {
        "status": "fonts_available",
        "primary_font": font_info['available_fonts'][0]['name'],
        "font_path": font_info['available_fonts'][0]['file'],
        "css_font_family": get_css_font_families(),
    }


# 模块初始化时记录字体信息
if logger.isEnabledFor(logging.INFO):
    try:
        log_font_info()
    except Exception as e:
        logger.warning(f"Failed to log font info: {e}")
