#!/usr/bin/env python
"""
内容库初始化CLI工具 - AI英语教学系统

提供内容库初始化、导入、索引、去重、验证和统计功能

用法:
    python scripts/init_content_library.py init --all          # 完整初始化
    python scripts/init_content_library.py import --content data/contents/
    python scripts/init_content_library.py index --batch-size 50
    python scripts/init_content_library.py deduplicate         # 语义去重
    python scripts/init_content_library.py validate --content data/contents/
    python scripts/init_content_library.py stats              # 查看统计
    python scripts/init_content_library.py update --file new_contents.json  # 增量更新
"""
import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加backend到路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import async_session
from app.services.content_import_service import ContentImportService, VocabularyImportService
from app.services.vector_service import VectorService
from app.services.content_deduplication_service import (
    ContentDeduplicationService,
    VocabularyDeduplicationService
)
from app.utils.content_validators import get_content_validator, get_vocabulary_validator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="内容库初始化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init命令
    init_parser = subparsers.add_parser("init", help="完整初始化")
    init_parser.add_argument("--content", type=str, help="内容JSON文件/目录")
    init_parser.add_argument("--vocabulary", type=str, help="词汇JSON文件/目录")
    init_parser.add_argument("--skip-index", action="store_true", help="跳过向量索引")
    init_parser.add_argument("--skip-duplicates", action="store_true", help="跳过去重")

    # import命令
    import_parser = subparsers.add_parser("import", help="导入内容")
    import_parser.add_argument("--content", type=str, help="内容JSON文件/目录")
    import_parser.add_argument("--vocabulary", type=str, help="词汇JSON文件/目录")
    import_parser.add_argument("--skip-duplicates", action="store_true", help="跳过去重")

    # index命令
    index_parser = subparsers.add_parser("index", help="向量索引")
    index_parser.add_argument("--batch-size", type=int, default=50, help="批处理大小")
    index_parser.add_argument("--content-id", type=str, action="append", help="指定内容ID")
    index_parser.add_argument("--all", action="store_true", help="索引所有未索引的内容")

    # deduplicate命令
    deduplicate_parser = subparsers.add_parser("deduplicate", help="执行语义去重")
    deduplicate_parser.add_argument("--content", action="store_true", help="对内容去重")
    deduplicate_parser.add_argument("--vocabulary", action="store_true", help="对词汇去重")
    deduplicate_parser.add_argument("--threshold", type=float, default=0.85, help="相似度阈值")

    # validate命令
    validate_parser = subparsers.add_parser("validate", help="验证数据")
    validate_parser.add_argument("--content", type=str, help="内容JSON文件/目录")
    validate_parser.add_argument("--vocabulary", type=str, help="词汇JSON文件/目录")

    # stats命令
    subparsers.add_parser("stats", help="查看统计信息")

    # update命令
    update_parser = subparsers.add_parser("update", help="增量更新")
    update_parser.add_argument("--file", type=str, required=True, help="新内容JSON文件")
    update_parser.add_argument("--index", action="store_true", help="同时索引新内容")

    return parser.parse_args()


async def progress_callback(phase: str, current: int, total: int, message: str):
    """进度回调"""
    if total == 0:
        print(f"\r{phase:12s} - {message}", end="", flush=True)
        return

    percent = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * percent // 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r{phase:12s} |{bar}| {current}/{total} ({percent:.1f}%) - {message}", end="", flush=True)
    if phase == "complete":
        print()


async def cmd_init(args):
    """init命令处理"""
    print("Starting content library initialization...")

    async with async_session() as db:
        vector_service = VectorService()
        import_service = ContentImportService(db, vector_service)

        # 导入内容
        if args.content:
            success, failed = await import_service.import_from_file(
                args.content, not args.skip_duplicates
            )
            print(f"\nContent import: {success} success, {failed} failed")

        # 导入词汇
        if args.vocabulary:
            vocab_service = VocabularyImportService(db, vector_service)
            success, failed = await vocab_service.import_from_file(
                args.vocabulary, not args.skip_duplicates
            )
            print(f"\nVocabulary import: {success} success, {failed} failed")

        # 索引向量
        if not args.skip_index:
            print("\nIndexing vectors...")
            stats = await vector_service.batch_index_contents(
                db, batch_size=50, progress_callback=progress_callback
            )
            print(f"\nIndex results: {stats}")


async def cmd_import(args):
    """import命令处理"""
    async with async_session() as db:
        vector_service = VectorService()

        if args.content:
            import_service = ContentImportService(db, vector_service)
            success, failed = await import_service.import_from_file(
                args.content, not args.skip_duplicates
            )
            print(f"Content import: {success} success, {failed} failed")

        if args.vocabulary:
            vocab_service = VocabularyImportService(db, vector_service)
            success, failed = await vocab_service.import_from_file(
                args.vocabulary, not args.skip_duplicates
            )
            print(f"Vocabulary import: {success} success, {failed} failed")


async def cmd_index(args):
    """index命令处理"""
    import uuid

    async with async_session() as db:
        vector_service = VectorService()

        content_ids = None
        if args.content_id:
            content_ids = [uuid.UUID(id) for id in args.content_id]

        if not args.content_id and not args.all:
            print("Please specify --content-id or --all")
            return

        print("Indexing vectors...")
        stats = await vector_service.batch_index_contents(
            db,
            content_ids=content_ids,
            batch_size=args.batch_size,
            progress_callback=progress_callback
        )
        print(f"\nIndex results: {stats}")


async def cmd_deduplicate(args):
    """deduplicate命令处理"""
    if not args.content and not args.vocabulary:
        print("Please specify --content and/or --vocabulary")
        return

    if args.content:
        print("Deduplicating contents...")
        deduplication_service = ContentDeduplicationService(
            similarity_threshold=args.threshold
        )

        # 加载现有内容
        from app.models.content import Content
        from sqlalchemy import select

        async with async_session() as db:
            result = await db.execute(select(Content))
            contents = result.scalars().all()

            if not contents:
                print("No contents found to deduplicate")
                return

            contents_data = [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "description": c.description,
                    "content_text": c.content_text,
                    "topic": c.topic,
                    "tags": c.tags or [],
                }
                for c in contents
            ]

            duplicates = await deduplication_service.find_duplicates(
                [c["title"] for c in contents_data],
                progress_callback
            )

            if duplicates:
                print(f"\nFound {len(duplicates)} duplicate groups:")
                for i, group in enumerate(duplicates):
                    print(f"  Group {i + 1}: {[contents_data[j]['title'] for j in group]}")
            else:
                print("No duplicates found")

    if args.vocabulary:
        print("\nDeduplicating vocabularies...")
        deduplication_service = VocabularyDeduplicationService(
            similarity_threshold=args.threshold
        )

        from app.models.content import Vocabulary
        from sqlalchemy import select

        async with async_session() as db:
            result = await db.execute(select(Vocabulary))
            vocabularies = result.scalars().all()

            if not vocabularies:
                print("No vocabularies found to deduplicate")
                return

            duplicates = await deduplication_service.find_duplicates([
                {"word": v.word, "definitions": v.definitions or []}
                for v in vocabularies
            ])

            if duplicates:
                print(f"\nFound {len(duplicates)} duplicate groups:")
                for i, group in enumerate(duplicates):
                    print(f"  Group {i + 1}: {[vocabularies[j].word for j in group]}")
            else:
                print("No duplicates found")


async def cmd_validate(args):
    """validate命令处理"""
    if not args.content and not args.vocabulary:
        print("Please specify --content and/or --vocabulary")
        return

    if args.content:
        path = Path(args.content)
        if path.is_file():
            validator = get_content_validator()
            success, errors = validator.validate_file(str(path))
            print(f"Validation of {path}: {'PASSED' if success else 'FAILED'}")
            if errors:
                for error in errors:
                    print(f"  - {error}")
        elif path.is_dir():
            print(f"Validating all JSON files in {path}...")
            json_files = list(path.glob("**/*.json"))
            passed = 0
            failed = 0
            for json_file in json_files:
                validator = get_content_validator()
                success, errors = validator.validate_file(str(json_file))
                if success:
                    passed += 1
                    print(f"  ✓ {json_file.relative_to(path)}")
                else:
                    failed += 1
                    print(f"  ✗ {json_file.relative_to(path)}: {errors[0]}")
            print(f"\nResults: {passed} passed, {failed} failed")

    if args.vocabulary:
        path = Path(args.vocabulary)
        if path.is_file():
            validator = get_vocabulary_validator()
            success, errors = validator.validate_file(str(path))
            print(f"Validation of {path}: {'PASSED' if success else 'FAILED'}")
            if errors:
                for error in errors:
                    print(f"  - {error}")
        elif path.is_dir():
            print(f"Validating all JSON files in {path}...")
            json_files = list(path.glob("**/*.json"))
            passed = 0
            failed = 0
            for json_file in json_files:
                validator = get_vocabulary_validator()
                success, errors = validator.validate_file(str(json_file))
                if success:
                    passed += 1
                    print(f"  ✓ {json_file.relative_to(path)}")
                else:
                    failed += 1
                    print(f"  ✗ {json_file.relative_to(path)}: {errors[0]}")
            print(f"\nResults: {passed} passed, {failed} failed")


async def cmd_stats(args):
    """stats命令处理"""
    async with async_session() as db:
        import_service = ContentImportService(db)
        stats = await import_service.get_import_stats()

        print("\n=== Content Library Statistics ===")
        print("\n📚 Contents by Type:")
        for content_type, count in stats.items():
            if content_type != '_total':
                print(f"  {content_type}: {count}")
        print(f"\n  Total: {stats.get('_total', 0)}")

        # 词汇统计
        from app.models.content import Vocabulary
        from sqlalchemy import select, func

        result = await db.execute(select(func.count(Vocabulary.id)))
        vocab_count = result.scalar()
        print(f"\n📖 Vocabularies: {vocab_count}")


async def cmd_update(args):
    """update命令处理"""
    async with async_session() as db:
        import_service = ContentImportService(db)

        success, failed = await import_service.import_from_file(args.file)
        print(f"Update import: {success} success, {failed} failed")

        if args.index:
            vector_service = VectorService()
            stats = await vector_service.batch_index_contents(
                db, batch_size=50, progress_callback=progress_callback
            )
            print(f"Index results: {stats}")


async def main():
    """主函数"""
    args = parse_args()

    if not args.command:
        print("Please specify a command. Use --help for usage.")
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "import": cmd_import,
        "index": cmd_index,
        "deduplicate": cmd_deduplicate,
        "validate": cmd_validate,
        "stats": cmd_stats,
        "update": cmd_update,
    }

    command = commands.get(args.command)
    if command:
        await command(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
