import asyncio
import os
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from edge_tts import Communicate, list_voices


class TTSEngine:
    CHINESE_VOICES = [
        {"name": "zh-CN-XiaoxiaoNeural", "description": "女声，自然流畅", "gender": "Female"},
        {"name": "zh-CN-YunyangNeural", "description": "男声，新闻播报风格", "gender": "Male"},
        {"name": "zh-CN-YunxiNeural", "description": "男声，年轻活泼", "gender": "Male"},
        {"name": "zh-CN-XiaoyiNeural", "description": "女声，温柔甜美", "gender": "Female"},
    ]

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        self.voice = voice
        self._validate_voice(voice)

    def _validate_voice(self, voice: str) -> None:
        valid_voices = [v["name"] for v in self.CHINESE_VOICES]
        if voice not in valid_voices:
            raise ValueError(f"无效的语音: {voice}。可用语音: {valid_voices}")

    async def text_to_speech(self, text: str, output_path: str) -> bool:
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            communicate = Communicate(text, self.voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            print(f"TTS 转换失败: {e}")
            return False

    def text_to_speech_sync(self, text: str, output_path: str) -> bool:
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            communicate = Communicate(text, self.voice)
            communicate.save_sync(output_path)
            return True
        except Exception as e:
            print(f"TTS 转换失败: {e}")
            return False

    @staticmethod
    def get_available_voices(language: str = "zh") -> list[dict]:
        if language == "zh":
            return TTSEngine.CHINESE_VOICES.copy()
        return []

    @staticmethod
    async def get_all_voices_async() -> list[dict]:
        voices = await list_voices()
        return voices

    @staticmethod
    def get_all_voices_sync() -> list[dict]:
        return asyncio.run(TTSEngine.get_all_voices_async())


# === 注册到引擎中心 ===
from .registry import TTSEngineRegistry, EngineMeta

TTSEngineRegistry.register(EngineMeta(
    engine_id="edge-tts",
    display_name="Edge-TTS (微软免费)",
    engine_cls=TTSEngine,
    voices=TTSEngine.CHINESE_VOICES,
    default_voice="zh-CN-XiaoxiaoNeural",
))


if __name__ == "__main__":
    test_text = "你好，这是一个测试。"
    output_file = os.path.join(os.path.dirname(__file__), "test_output.mp3")

    print(f"测试文本: {test_text}")
    print(f"输出文件: {output_file}")

    engine = TTSEngine()
    print(f"使用语音: {engine.voice}")

    success = engine.text_to_speech_sync(test_text, output_file)

    if success:
        print(f"音频文件生成成功: {output_file}")
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"文件大小: {file_size} 字节")
    else:
        print("音频文件生成失败")
