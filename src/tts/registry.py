"""
TTS 引擎注册中心

自动发现 src/tts/ 下的引擎模块，各引擎通过 register() 自注册。
新增引擎只需新建文件 + 调用 register()，无需修改主流程代码。

使用方式:
    from tts.registry import TTSEngineRegistry

    # 获取所有已注册引擎
    engines = TTSEngineRegistry.list_engines()

    # 创建引擎实例
    tts = TTSEngineRegistry.create_engine("minimax", voice_id="female-shaonv")

    # 获取引擎语音列表
    voices = TTSEngineRegistry.get_voices("edge-tts")
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class EngineMeta:
    """引擎注册元信息"""
    engine_id: str
    display_name: str
    engine_cls: Type
    voices: List[dict] = field(default_factory=list)
    default_voice: str = ""
    is_available: Optional[Callable[[], bool]] = None


class TTSEngineRegistry:
    """TTS 引擎注册中心（单例模式）"""

    _engines: Dict[str, EngineMeta] = {}
    _discovered: bool = False

    @classmethod
    def _discover(cls) -> None:
        """自动扫描 src/tts/ 包，触发各引擎模块的 register() 调用"""
        if cls._discovered:
            return
        cls._discovered = True

        try:
            from . import tts_engine  # noqa: F401
        except Exception as e:
            logger.debug(f"Edge-TTS 引擎加载跳过: {e}")

        try:
            from . import chat_tts_converter  # noqa: F401
        except Exception as e:
            logger.debug(f"ChatTTS 引擎加载跳过: {e}")

        try:
            from . import minimax_tts  # noqa: F401
        except Exception as e:
            logger.debug(f"Minimax 引擎加载跳过: {e}")

        try:
            from . import doubao_tts  # noqa: F401
        except Exception as e:
            logger.debug(f"豆包引擎加载跳过: {e}")

    @classmethod
    def register(cls, meta: EngineMeta) -> None:
        """注册一个 TTS 引擎"""
        cls._engines[meta.engine_id] = meta
        logger.info(f"TTS引擎已注册: {meta.engine_id} ({meta.display_name})")

    @classmethod
    def list_engines(cls) -> Dict[str, str]:
        """返回已注册引擎 {engine_id: display_name}"""
        cls._discover()
        return {k: v.display_name for k, v in cls._engines.items()}

    @classmethod
    def get_engine(cls, engine_id: str) -> Optional[EngineMeta]:
        """获取引擎元信息"""
        cls._discover()
        return cls._engines.get(engine_id)

    @classmethod
    def create_engine(cls, engine_id: str, **kwargs) -> Any:
        """
        创建引擎实例。

        Args:
            engine_id: 引擎标识符
            **kwargs: 传递给引擎构造函数的参数 (voice, voice_id, use_gpu 等)

        Returns:
            引擎实例，具有 text_to_speech(text, output_path) -> bool 方法

        Raises:
            ValueError: 引擎未注册或创建失败
        """
        meta = cls.get_engine(engine_id)
        if not meta:
            available = list(cls.list_engines().keys())
            raise ValueError(f"未找到TTS引擎: {engine_id}，可用: {available}")

        if meta.is_available and not meta.is_available():
            raise ValueError(f"TTS引擎 {engine_id} 不可用，请检查依赖安装")

        engine_cls = meta.engine_cls

        # 根据引擎类型传递对应的参数
        if engine_id == "edge-tts":
            voice = kwargs.get("voice", meta.default_voice)
            return engine_cls(voice=voice)
        elif engine_id == "chat-tts":
            use_gpu = kwargs.get("use_gpu", True)
            return engine_cls(use_gpu=use_gpu)
        elif engine_id == "minimax":
            voice_id = kwargs.get("voice", None) or kwargs.get("voice_id", None) or meta.default_voice
            return engine_cls(voice_id=voice_id)
        elif engine_id == "doubao":
            speaker = kwargs.get("voice", None) or kwargs.get("speaker", None) or meta.default_voice
            return engine_cls(speaker=speaker)
        else:
            # 通用创建：尝试用 voice 参数
            voice = kwargs.get("voice", meta.default_voice)
            if hasattr(engine_cls, "__init__"):
                import inspect
                sig = inspect.signature(engine_cls.__init__)
                if "voice" in sig.parameters:
                    return engine_cls(voice=voice)
            return engine_cls(**kwargs)

    @classmethod
    def get_voices(cls, engine_id: str) -> List[dict]:
        """获取引擎的语音/音色列表"""
        meta = cls.get_engine(engine_id)
        if not meta:
            return []
        return meta.voices

    @classmethod
    def get_default_voice(cls, engine_id: str) -> str:
        """获取引擎的默认语音"""
        meta = cls.get_engine(engine_id)
        if not meta:
            return ""
        return meta.default_voice
