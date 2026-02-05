#!/usr/bin/env python3
"""
运行教案模板初始化的便捷脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from init_lesson_templates import init_lesson_templates
import asyncio


async def main():
    """主函数"""
    try:
        await init_lesson_templates()
        print("\n✅ 教案模板初始化完成！")
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
