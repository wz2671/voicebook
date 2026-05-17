import asyncio
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from loguru import logger

from .tts_engine import TTSEngine


class AudioConverter:
    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        self.tts_engine = TTSEngine(voice)
        self.voice = voice

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

    def split_text(self, text: str, max_length: int = 5000) -> list[str]:
        if len(text) <= max_length:
            return [text] if text.strip() else []

        paragraphs = text.split('\n\n')
        segments = []
        current_segment = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_segment) + len(para) + 2 <= max_length:
                if current_segment:
                    current_segment += "\n\n" + para
                else:
                    current_segment = para
            else:
                if current_segment:
                    segments.append(current_segment)

                if len(para) > max_length:
                    sentences = re.split(r'([。！？；\n])', para)
                    temp_segment = ""

                    for i in range(0, len(sentences), 2):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i + 1]

                        if len(temp_segment) + len(sentence) <= max_length:
                            temp_segment += sentence
                        else:
                            if temp_segment:
                                segments.append(temp_segment)
                            temp_segment = sentence

                    if temp_segment:
                        if len(current_segment) + len(temp_segment) + 2 <= max_length and current_segment:
                            current_segment = current_segment + "\n\n" + temp_segment
                        else:
                            if current_segment:
                                segments.append(current_segment)
                            current_segment = temp_segment
                else:
                    current_segment = para

        if current_segment:
            segments.append(current_segment)

        return segments

    def _merge_audio_files(self, audio_files: list[str], output_path: str) -> bool:
        if not audio_files:
            return False

        if len(audio_files) == 1:
            if audio_files[0] != output_path:
                shutil.move(audio_files[0], output_path)
            return True

        try:
            list_file = output_path + ".txt"
            with open(list_file, 'w', encoding='utf-8') as f:
                for audio_file in audio_files:
                    f.write(f"file '{os.path.abspath(audio_file)}'\n")

            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy', output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            os.remove(list_file)
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    os.remove(audio_file)

            if result.returncode == 0:
                logger.info(f"音频合并成功: {output_path}")
                return True
            else:
                logger.error(f"音频合并失败: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.warning("ffmpeg 未安装，尝试使用备用合并方法")
            return self._merge_audio_files_simple(audio_files, output_path)
        except Exception as e:
            logger.error(f"音频合并失败: {e}")
            return False

    def _merge_audio_files_simple(self, audio_files: list[str], output_path: str) -> bool:
        try:
            with open(output_path, 'wb') as outfile:
                for i, audio_file in enumerate(audio_files):
                    with open(audio_file, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(audio_file)

            logger.info(f"音频合并成功 (简单模式): {output_path}")
            return True
        except Exception as e:
            logger.error(f"简单合并失败: {e}")
            return False

    async def convert_chapter_async(self, md_path: str, output_path: str) -> bool:
        try:
            logger.info(f"开始转换章节: {md_path}")

            text = self.read_markdown(md_path)
            if not text:
                logger.warning(f"章节内容为空: {md_path}")
                return False

            segments = self.split_text(text)
            if not segments:
                logger.warning(f"分段后无有效内容: {md_path}")
                return False

            logger.info(f"文本已分为 {len(segments)} 段")

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            temp_dir = tempfile.mkdtemp()
            audio_files = []

            for i, segment in enumerate(segments, 1):
                temp_output = os.path.join(temp_dir, f"segment_{i:03d}.mp3")
                logger.info(f"转换第 {i}/{len(segments)} 段 ({len(segment)} 字符)...")

                success = await self.tts_engine.text_to_speech(segment, temp_output)
                if success:
                    audio_files.append(temp_output)
                    logger.info(f"第 {i} 段转换成功")
                else:
                    logger.error(f"第 {i} 段转换失败")

            if not audio_files:
                logger.error("所有分段转换失败")
                return False

            success = self._merge_audio_files(audio_files, output_path)

            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except:
                    pass

            if success:
                logger.info(f"章节转换完成: {output_path}")
            return success

        except Exception as e:
            logger.error(f"章节转换失败: {e}")
            return False

    def convert_chapter(self, md_path: str, output_path: str) -> bool:
        return asyncio.run(self.convert_chapter_async(md_path, output_path))

    def convert_book(self, chapter_dir: str, output_dir: str, book_name: str) -> list[str]:
        chapter_path = Path(chapter_dir)
        if not chapter_path.exists():
            logger.error(f"章节目录不存在: {chapter_dir}")
            return []

        md_files = sorted(chapter_path.glob("*.md"))
        if not md_files:
            logger.warning(f"未找到章节文件: {chapter_dir}")
            return []

        book_output_dir = Path(output_dir) / book_name
        book_output_dir.mkdir(parents=True, exist_ok=True)

        success_files = []
        total = len(md_files)

        for i, md_file in enumerate(md_files, 1):
            output_file = book_output_dir / f"{md_file.stem}.mp3"

            logger.info(f"\n{'='*50}")
            logger.info(f"进度: [{i}/{total}] {md_file.name}")
            logger.info(f"{'='*50}")

            if output_file.exists():
                logger.info(f"音频文件已存在，跳过: {output_file}")
                success_files.append(str(output_file))
                continue

            success = self.convert_chapter(str(md_file), str(output_file))
            if success:
                success_files.append(str(output_file))

        logger.info(f"\n转换完成: {len(success_files)}/{total} 个章节")
        return success_files


if __name__ == "__main__":
    import sys

    base_dir = Path(__file__).parent.parent.parent
    chapter_path = base_dir / "chapter" / "三体(全三册)" / "chapter1.md"
    output_path = base_dir / "audios" / "三体(全三册)" / "chapter1.mp3"

    print(f"测试文件: {chapter_path}")
    print(f"输出路径: {output_path}")
    print(f"使用语音: zh-CN-XiaoxiaoNeural")
    print("-" * 50)

    converter = AudioConverter()

    success = converter.convert_chapter(str(chapter_path), str(output_path))

    if success:
        print(f"\n转换成功!")
        print(f"音频文件: {output_path}")
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"文件大小: {file_size / 1024:.2f} KB")
    else:
        print("\n转换失败!")
        sys.exit(1)
