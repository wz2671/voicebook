"""
电子书解析器注册中心

自动发现解析器模块，各解析器通过 register() 自注册。
新增解析器只需新建文件 + 调用 register()，无需修改主流程代码。

使用方式:
    from parser.registry import ParserRegistry

    # 检查是否支持某格式
    if ParserRegistry.is_supported(".epub"):
        ...

    # 执行解析
    saved_files, tempdir = ParserRegistry.parse("book.epub", "output_dir")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParserMeta:
    """解析器注册元信息"""
    ext: str              # 文件扩展名，含点号 如 ".mobi", ".epub"
    display_name: str     # 显示名 如 "MOBI", "EPUB"
    process_fn: Callable[..., Tuple[list, Any]]
    # process_fn 签名: (file_path: str, output_dir: str) -> (saved_files: list, tempdir: str)


class ParserRegistry:
    """电子书解析器注册中心"""

    _parsers: Dict[str, ParserMeta] = {}
    _discovered: bool = False

    @classmethod
    def _discover(cls) -> None:
        """自动扫描并触发解析器模块的 register() 调用"""
        if cls._discovered:
            return
        cls._discovered = True

        try:
            from mobi_handler import mobi_extractor  # noqa: F401
        except Exception as e:
            logger.debug(f"MOBI 解析器加载跳过: {e}")

        try:
            from epub_handler import epub_extractor  # noqa: F401
        except Exception as e:
            logger.debug(f"EPUB 解析器加载跳过: {e}")

    @classmethod
    def register(cls, meta: ParserMeta) -> None:
        """注册一个解析器"""
        cls._parsers[meta.ext] = meta
        logger.info(f"解析器已注册: {meta.ext} ({meta.display_name})")

    @classmethod
    def is_supported(cls, ext: str) -> bool:
        """检查是否支持指定扩展名"""
        cls._discover()
        return ext.lower() in cls._parsers

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """获取所有支持的扩展名"""
        cls._discover()
        return list(cls._parsers.keys())

    @classmethod
    def get_parser(cls, ext: str) -> Optional[ParserMeta]:
        """获取指定扩展名的解析器元信息"""
        cls._discover()
        return cls._parsers.get(ext.lower())

    @classmethod
    def parse(cls, file_path: str, output_dir: str) -> Tuple[list, Any]:
        """
        解析电子书文件。

        Args:
            file_path: 电子书文件路径
            output_dir: 输出目录

        Returns:
            (saved_files, tempdir)

        Raises:
            ValueError: 不支持的格式
        """
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        meta = cls.get_parser(ext)
        if not meta:
            supported = ", ".join(cls.get_supported_extensions())
            raise ValueError(f"不支持的文件格式 ({ext})，仅支持: {supported}")

        return meta.process_fn(file_path, output_dir)
