import argparse
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_libs_path = str(Path(__file__).parent / "libs")
if _libs_path not in sys.path:
    sys.path.insert(0, _libs_path)

sys.path.insert(0, str(Path(__file__).parent))

from config import AUDIO_FORMAT, AUDIOS_DIR, BOOKS_DIR, CHAPTER_DIR, PROJECT_ROOT, ensure_dirs
from env import env as _env
from mobi_handler.mobi_extractor import process_mobi
from tts.tts_engine import TTSEngine


def setup_logging(log_dir: Optional[str] = None) -> logging.Logger:
    if log_dir is None:
        log_dir = PROJECT_ROOT / "logs"

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / f"voicebook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logger = logging.getLogger("voicebook")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class ProgressBar:
    def __init__(self, total: int, desc: str = "Processing", width: int = 50):
        self.total = total
        self.desc = desc
        self.width = width
        self.current = 0
        self.start_time = time.time()

    def update(self, n: int = 1, current_item: str = ""):
        self.current += n
        percent = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        bar = '█' * filled + '░' * (self.width - filled)

        elapsed = time.time() - self.start_time
        if self.current > 0 and self.current < self.total:
            eta = elapsed / self.current * (self.total - self.current)
            eta_str = self._format_time(eta)
        else:
            eta_str = "--:--"

        item_display = f" - {current_item[:30]}" if current_item else ""

        sys.stdout.write('\r')
        sys.stdout.write(
            f"{self.desc}: |{bar}| {self.current}/{self.total} "
            f"({percent*100:.1f}%) ETA: {eta_str}{item_display}"
        )
        sys.stdout.flush()

        if self.current >= self.total:
            sys.stdout.write('\n')
            elapsed_str = self._format_time(elapsed)
            print(f"完成! 总用时: {elapsed_str}")

    def _format_time(self, seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


def extract_command(mobi_path: str, output_dir: str, logger: logging.Logger) -> int:
    logger.info(f"开始提取MOBI文件: {mobi_path}")

    mobi_file = Path(mobi_path)
    if not mobi_file.exists():
        logger.error(f"MOBI文件不存在: {mobi_path}")
        print(f"错误: MOBI文件不存在: {mobi_path}")
        return 1

    if not mobi_file.suffix.lower() == '.mobi':
        logger.error(f"文件不是MOBI格式: {mobi_path}")
        print(f"错误: 文件不是MOBI格式: {mobi_path}")
        return 1

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tempdir = None
    try:
        print(f"\n正在提取: {mobi_file.name}")
        saved_files, tempdir = process_mobi(str(mobi_file), str(output_path))

        if not saved_files:
            logger.warning("没有提取到任何章节")
            print("警告: 没有提取到任何章节")
            return 1

        logger.info(f"成功提取 {len(saved_files)} 个章节")
        print(f"\n成功提取 {len(saved_files)} 个章节")
        print(f"输出目录: {output_path / mobi_file.stem}")

        print("\n章节列表:")
        for i, file in enumerate(saved_files[:10], 1):
            with open(file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                title = first_line.replace('# ', '') if first_line.startswith('# ') else first_line
                print(f"  {i}. {title}")

        if len(saved_files) > 10:
            print(f"  ... 还有 {len(saved_files) - 10} 个章节")

        return 0

    except Exception as e:
        logger.exception(f"提取失败: {e}")
        print(f"\n错误: 提取失败 - {e}")
        return 1

    finally:
        if tempdir and os.path.exists(tempdir):
            shutil.rmtree(tempdir, ignore_errors=True)
            logger.debug(f"已清理临时目录: {tempdir}")


def convert_command(chapter_dir: str, output_dir: str, voice: str, engine: str, logger: logging.Logger) -> int:
    logger.info(f"开始转换音频: {chapter_dir}")
    logger.info(f"使用引擎: {engine}, 语音: {voice}")

    chapter_path = Path(chapter_dir)
    if not chapter_path.exists():
        logger.error(f"章节目录不存在: {chapter_dir}")
        print(f"错误: 章节目录不存在: {chapter_dir}")
        return 1

    chapter_files = sorted(chapter_path.glob("chapter*.md"))
    if not chapter_files:
        logger.error(f"没有找到章节文件: {chapter_dir}")
        print(f"错误: 没有找到章节文件 (chapter*.md)")
        return 1

    book_name = chapter_path.name
    output_path = Path(output_dir) / book_name
    output_path.mkdir(parents=True, exist_ok=True)

    if engine == 'edge-tts':
        voice_name = voice or _env.edge_tts_default_voice
        try:
            tts = TTSEngine(voice=voice_name)
            logger.info(f"TTS引擎初始化成功，语音: {voice_name}")
        except ValueError as e:
            logger.error(f"无效的语音选择: {voice_name}")
            print(f"错误: {e}")
            print("\n可用的中文语音:")
            for v in TTSEngine.get_available_voices("zh"):
                print(f"  - {v['name']}: {v['description']}")
            return 1
    elif engine == 'chat-tts':
        from tts.chat_tts_converter import ChatTTSConverter
        if not ChatTTSConverter.is_available():
            logger.error("ChatTTS不可用，请安装依赖: pip install torch torchaudio")
            print("错误: ChatTTS不可用，请安装依赖: pip install torch torchaudio")
            return 1
        tts = ChatTTSConverter(use_gpu=_env.chat_tts_use_gpu)
        logger.info("ChatTTS引擎初始化成功")
    elif engine == 'minimax':
        from tts.minimax_tts import MinimaxTTS
        if not MinimaxTTS.is_available():
            logger.error("Minimax TTS不可用，请安装依赖: pip install requests")
            print("错误: Minimax TTS不可用，请安装依赖: pip install requests")
            return 1
        try:
            voice_id = voice or _env.minimax_voice_id
            tts = MinimaxTTS(voice_id=voice_id)
            logger.info(f"Minimax TTS引擎初始化成功，音色: {tts.voice_id}")
        except ValueError as e:
            logger.error(f"Minimax TTS初始化失败: {e}")
            print(f"错误: {e}")
            return 1

    if engine == 'edge-tts':
        display_voice = voice or _env.edge_tts_default_voice
    elif engine == 'minimax':
        display_voice = voice or _env.minimax_voice_id
    else:
        display_voice = voice or ""

    print(f"\n开始转换 {len(chapter_files)} 个章节")
    print(f"使用引擎: {engine}")
    if engine == 'edge-tts':
        print(f"使用语音: {display_voice}")
    elif engine == 'minimax':
        print(f"使用音色ID: {display_voice}")
    print(f"输出目录: {output_path}")
    print()

    progress = ProgressBar(len(chapter_files), desc="转换进度")
    success_count = 0
    failed_count = 0

    for chapter_file in chapter_files:
        chapter_name = chapter_file.stem
        audio_file = output_path / f"{chapter_name}.{AUDIO_FORMAT}"

        try:
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            title = lines[0].replace('# ', '') if lines and lines[0].startswith('# ') else chapter_name
            text_content = '\n'.join(lines[1:]).strip()

            if not text_content:
                logger.warning(f"章节内容为空: {chapter_file}")
                progress.update(1, title)
                failed_count += 1
                continue

            logger.debug(f"转换章节: {title}")

            if engine == 'edge-tts':
                success = tts.text_to_speech_sync(text_content, str(audio_file))
            elif engine == 'chat-tts' or engine == 'minimax':
                success = tts.text_to_speech(text_content, str(audio_file))

            if success:
                success_count += 1
                logger.info(f"成功转换: {title} -> {audio_file}")
            else:
                failed_count += 1
                logger.error(f"转换失败: {title}")

            progress.update(1, title)

        except Exception as e:
            failed_count += 1
            logger.exception(f"处理章节失败 {chapter_file}: {e}")
            progress.update(1, chapter_name)

    print()
    print(f"转换完成: 成功 {success_count}, 失败 {failed_count}")
    logger.info(f"转换完成: 成功 {success_count}, 失败 {failed_count}")

    return 0 if failed_count == 0 else 1


def process_command(mobi_path: str, output_dir: str, voice: str, engine: str, logger: logging.Logger) -> int:
    logger.info(f"开始完整流程: {mobi_path}")

    mobi_file = Path(mobi_path)
    if not mobi_file.exists():
        logger.error(f"MOBI文件不存在: {mobi_path}")
        print(f"错误: MOBI文件不存在: {mobi_path}")
        return 1

    book_name = mobi_file.stem
    chapter_output = Path(output_dir) / "chapter" / book_name
    audio_output = Path(output_dir) / "audios"

    print(f"\n{'='*60}")
    print(f"开始处理: {mobi_file.name}")
    print(f"{'='*60}")

    print("\n[步骤 1/2] 提取章节...")
    extract_result = extract_command(mobi_path, str(Path(output_dir) / "chapter"), logger)

    if extract_result != 0:
        logger.error("提取步骤失败，终止流程")
        return extract_result

    print("\n[步骤 2/2] 转换音频...")
    convert_result = convert_command(str(chapter_output), str(audio_output), voice, engine, logger)

    if convert_result != 0:
        logger.error("转换步骤失败")
        return convert_result

    print(f"\n{'='*60}")
    print("完整流程执行成功!")
    print(f"章节目录: {chapter_output}")
    print(f"音频目录: {audio_output / book_name}")
    print(f"{'='*60}")

    return 0


def list_voices_command():
    print("可用的中文语音:\n")
    voices = TTSEngine.get_available_voices("zh")
    for v in voices:
        print(f"  {v['name']}")
        print(f"    描述: {v['description']}")
        print(f"    性别: {v['gender']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog='voicebook',
        description='VoiceBook - MOBI电子书转音频工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s extract books/mybook.mobi                    # 提取章节到默认目录
  %(prog)s extract books/mybook.mobi -o ./output        # 提取章节到指定目录
  %(prog)s convert chapter/mybook                       # 转换章节为音频 (默认edge-tts)
  %(prog)s convert chapter/mybook -v zh-CN-YunxiNeural  # 使用指定语音
  %(prog)s convert chapter/mybook --engine chat-tts     # 使用ChatTTS引擎
  %(prog)s process books/mybook.mobi                    # 完整流程
  %(prog)s process books/mybook.mobi --engine chat-tts  # 完整流程使用ChatTTS
  %(prog)s process books/mybook.mobi --engine minimax   # 完整流程使用Minimax
  %(prog)s voices                                       # 列出可用语音
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    extract_parser = subparsers.add_parser('extract', help='从MOBI文件提取章节')
    extract_parser.add_argument('mobi_file', help='MOBI文件路径')
    extract_parser.add_argument('-o', '--output', default=str(CHAPTER_DIR),
                                help=f'输出目录 (默认: {CHAPTER_DIR})')

    convert_parser = subparsers.add_parser('convert', help='将章节转换为音频')
    convert_parser.add_argument('chapter_dir', help='章节目录路径')
    convert_parser.add_argument('-o', '--output', default=str(AUDIOS_DIR),
                                help=f'输出目录 (默认: {AUDIOS_DIR})')
    convert_parser.add_argument('-v', '--voice', default=None,
                                help=f'TTS语音/音色ID (默认: edge-tts={_env.edge_tts_default_voice}, minimax={_env.minimax_voice_id})')
    convert_parser.add_argument('--engine', choices=['edge-tts', 'chat-tts', 'minimax'], default='edge-tts',
                                help='TTS引擎 (默认: edge-tts)')

    process_parser = subparsers.add_parser('process', help='完整流程：提取+转换')
    process_parser.add_argument('mobi_file', help='MOBI文件路径')
    process_parser.add_argument('-o', '--output', default=str(PROJECT_ROOT),
                                help=f'输出根目录 (默认: {PROJECT_ROOT})')
    process_parser.add_argument('-v', '--voice', default=None,
                                help=f'TTS语音/音色ID (edge-tts默认: {_env.edge_tts_default_voice}, minimax默认: {_env.minimax_voice_id})')
    process_parser.add_argument('--engine', choices=['edge-tts', 'chat-tts', 'minimax'], default='edge-tts',
                                help='TTS引擎 (默认: edge-tts)')

    voices_parser = subparsers.add_parser('voices', help='列出可用的TTS语音')

    parser.add_argument('--log-dir', help='日志目录')
    parser.add_argument('--verbose', '-V', action='store_true', help='显示详细输出')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    ensure_dirs()

    logger = setup_logging(getattr(args, 'log_dir', None))

    if args.verbose:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)

    if args.command == 'extract':
        return extract_command(args.mobi_file, args.output, logger)

    elif args.command == 'convert':
        return convert_command(args.chapter_dir, args.output, args.voice, args.engine, logger)

    elif args.command == 'process':
        return process_command(args.mobi_file, args.output, args.voice, args.engine, logger)

    elif args.command == 'voices':
        list_voices_command()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
