"""
ChatTTS 文字转语音转换器

依赖安装:
    pip install torch torchaudio

注意事项:
    - ChatTTS需要下载约2GB的模型文件
    - 首次使用会自动下载模型到 ~/.cache/huggingface/
    - 推荐使用GPU以获得更好性能
    - CPU模式也可以运行，但速度较慢
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, List
import logging
import subprocess

libs_path = Path(__file__).parent.parent / "libs"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

logger = logging.getLogger(__name__)


class ChatTTSConverter:
    CHAT_TTS_AVAILABLE = False
    TORCH_AVAILABLE = False

    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.chat = None
        self.sample_rate = 24000
        self.device = "cpu"
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            import torch
            self.TORCH_AVAILABLE = True
            if self.use_gpu and torch.cuda.is_available():
                self.device = "cuda"
                logger.info("使用GPU模式")
            else:
                self.device = "cpu"
                logger.info("使用CPU模式")
        except ImportError:
            self.TORCH_AVAILABLE = False
            self.device = "cpu"
            logger.warning("torch未安装，将使用CPU模式")

        try:
            import chat_tts
            self.CHAT_TTS_AVAILABLE = True
            logger.info("ChatTTS库已加载")
        except ImportError as e:
            self.CHAT_TTS_AVAILABLE = False
            logger.warning(f"ChatTTS未安装或导入失败: {e}")

    @staticmethod
    def is_available() -> bool:
        try:
            import torch
            libs_path = Path(__file__).parent.parent / "libs"
            if str(libs_path) not in sys.path:
                sys.path.insert(0, str(libs_path))
            import chat_tts
            return True
        except ImportError:
            return False

    def load_model(self) -> bool:
        if not self.CHAT_TTS_AVAILABLE:
            logger.error("ChatTTS未安装，请检查依赖")
            return False

        if self.chat is not None:
            return True

        try:
            import chat_tts
            logger.info("正在加载ChatTTS模型...")

            self.chat = chat_tts.Chat()

            if self.device == "cuda":
                self.chat.load_models(
                    compile=False,
                    device="cuda"
                )
            else:
                self.chat.load_models(
                    compile=False,
                    device="cpu"
                )

            logger.info("ChatTTS模型加载成功")
            return True
        except Exception as e:
            logger.error(f"加载ChatTTS模型失败: {e}")
            return False

    def read_markdown(self, md_path: str) -> str:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(r'^#+\s+.*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            content = re.sub(r'`(.+?)`', r'\1', content)
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
            content = re.sub(r'^[-*+]\s+', '', content, flags=re.MULTILINE)
            content = re.sub(r'^\d+\.\s+', '', content, flags=re.MULTILINE)
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = content.strip()
            return content
        except Exception as e:
            logger.error(f"读取Markdown文件失败: {e}")
            raise

    def split_text(self, text: str, max_length: int = 200) -> List[str]:
        if len(text) <= max_length:
            return [text] if text.strip() else []

        segments = []
        paragraphs = text.split('\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) <= max_length:
                segments.append(para)
            else:
                sentences = []
                current = ""

                for char in para:
                    current += char
                    if char in ['。', '！', '？', '；', '.', '!', '?', ';', '\n']:
                        if len(current) >= 20:
                            sentences.append(current.strip())
                            current = ""

                if current.strip():
                    sentences.append(current.strip())

                for sent in sentences:
                    if len(sent) <= max_length:
                        segments.append(sent)
                    else:
                        for i in range(0, len(sent), max_length):
                            segments.append(sent[i:i+max_length])

        return [s for s in segments if s.strip()]

    def text_to_speech(self, text: str, output_path: str) -> bool:
        if not self.chat:
            if not self.load_model():
                return False

        try:
            import torch
            import torchaudio

            segments = self.split_text(text)
            if not segments:
                logger.warning("文本为空，跳过转换")
                return False

            logger.info(f"文本已分为 {len(segments)} 段")

            audio_segments = []

            for i, segment in enumerate(segments):
                if not segment.strip():
                    continue

                logger.info(f"转换第 {i+1}/{len(segments)} 段 ({len(segment)} 字符)...")

                try:
                    wavs = self.chat.infer([segment])

                    if wavs and len(wavs) > 0:
                        audio_segments.append(wavs[0])
                except Exception as e:
                    logger.warning(f"第 {i+1} 段转换失败: {e}")
                    continue

            if not audio_segments:
                logger.error("没有成功转换任何音频段")
                return False

            combined_audio = torch.cat(audio_segments, dim=1)

            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            if output_path.endswith('.mp3'):
                temp_wav = output_path.replace('.mp3', '.wav')
                torchaudio.save(temp_wav, combined_audio, self.sample_rate)
                self._wav_to_mp3(temp_wav, output_path)
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            else:
                torchaudio.save(output_path, combined_audio, self.sample_rate)

            logger.info(f"音频保存成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"转换失败: {e}")
            return False

    def _wav_to_mp3(self, wav_path: str, mp3_path: str):
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', wav_path, '-acodec', 'libmp3lame', '-y', mp3_path],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                logger.info(f"音频转换为MP3成功: {mp3_path}")
                return
        except FileNotFoundError:
            logger.warning("ffmpeg 未安装，保留WAV格式")
        except Exception as e:
            logger.warning(f"ffmpeg转换失败: {e}")

        import shutil
        wav_output = mp3_path.replace('.mp3', '.wav')
        shutil.copy(wav_path, wav_output)
        logger.info(f"音频保存为WAV格式: {wav_output}")

    def convert_chapter(self, md_path: str, output_path: str) -> bool:
        try:
            text = self.read_markdown(md_path)

            if not text:
                logger.warning(f"章节文件为空: {md_path}")
                return False

            return self.text_to_speech(text, output_path)

        except Exception as e:
            logger.error(f"转换章节失败: {e}")
            return False

    def convert_book(self, chapter_dir: str, output_dir: str, book_name: str) -> List[str]:
        chapter_path = Path(chapter_dir)
        output_path = Path(output_dir) / book_name
        output_path.mkdir(parents=True, exist_ok=True)

        md_files = sorted(chapter_path.glob("chapter*.md"))

        if not md_files:
            logger.warning(f"未找到章节文件: {chapter_dir}")
            return []

        success_files = []
        total = len(md_files)

        for i, md_file in enumerate(md_files, 1):
            logger.info(f"处理 {i}/{total}: {md_file.name}")

            audio_file = output_path / md_file.name.replace('.md', '.wav')

            if self.convert_chapter(str(md_file), str(audio_file)):
                success_files.append(str(audio_file))

        logger.info(f"转换完成: {len(success_files)}/{total} 个章节")
        return success_files


def create_chat_tts_converter(use_gpu: bool = True) -> Optional[ChatTTSConverter]:
    if not ChatTTSConverter.is_available():
        logger.warning("ChatTTS不可用，请安装依赖: pip install torch torchaudio")
        return None

    converter = ChatTTSConverter(use_gpu=use_gpu)
    return converter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if not ChatTTSConverter.is_available():
        print("ChatTTS未安装，请检查依赖")
        sys.exit(1)

    converter = ChatTTSConverter(use_gpu=True)

    test_text = "你好，这是一个测试。欢迎使用ChatTTS语音合成系统。"
    output_file = "test_chattts_output.wav"

    if converter.text_to_speech(test_text, output_file):
        print(f"测试成功，音频已保存到: {output_file}")
    else:
        print("测试失败")
