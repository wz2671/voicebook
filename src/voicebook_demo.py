"""
VoiceBook 使用示例集

本文件包含 VoiceBook 库的各种使用示例，
包括 MOBI 提取、TTS 转换、批量处理等。

使用方法：
    1. 直接运行本文件查看示例输出
    2. 复制需要的示例代码到自己的脚本中使用
    3. 根据需要修改参数和路径
"""

import sys
from pathlib import Path

libs_path = Path(__file__).parent / "libs"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))


# ============================================================================
# 示例1: 基本 MOBI 提取
# ============================================================================
"""
功能：从 MOBI 文件中提取文字内容，按章节分割输出

代码：
    from mobi_handler.mobi_extractor import process_mobi
    import shutil

    # 处理 MOBI 文件
    mobi_path = "books/三体(全三册).mobi"
    output_dir = "chapter"

    # 返回保存的文件列表和临时目录
    saved_files, tempdir = process_mobi(mobi_path, output_dir)

    print(f"提取了 {len(saved_files)} 个章节")

    # 清理临时目录
    shutil.rmtree(tempdir, ignore_errors=True)

预期输出：
    提取了 98 个章节
    章节文件保存在 chapter/三体(全三册)/ 目录下
"""


# ============================================================================
# 示例2: 提取并指定输出目录
# ============================================================================
"""
功能：指定自定义输出目录提取 MOBI 文件

代码：
    from mobi_handler.mobi_extractor import process_mobi
    import shutil

    mobi_path = "books/三体(全三册).mobi"
    custom_output = "output/my_book"

    saved_files, tempdir = process_mobi(mobi_path, custom_output)

    for file_path in saved_files[:5]:
        print(f"保存: {file_path}")

    shutil.rmtree(tempdir, ignore_errors=True)

预期输出：
    保存: output/my_book/三体(全三册)/chapter1.md
    保存: output/my_book/三体(全三册)/chapter2.md
    ...
"""


# ============================================================================
# 示例3: 使用 Edge-TTS 转换单个章节
# ============================================================================
"""
功能：使用 Edge-TTS 将单个章节 Markdown 文件转换为音频

代码：
    from tts.audio_converter import AudioConverter

    # 创建转换器，使用默认语音（zh-CN-XiaoxiaoNeural）
    converter = AudioConverter()

    # 转换单个章节
    md_path = "chapter/三体(全三册)/chapter1.md"
    audio_path = "audios/三体(全三册)/chapter1.mp3"

    success = converter.convert_chapter(md_path, audio_path)

    if success:
        print(f"转换成功: {audio_path}")
    else:
        print("转换失败")

预期输出：
    转换成功: audios/三体(全三册)/chapter1.mp3
"""


# ============================================================================
# 示例4: 使用 Edge-TTS 转换整本书
# ============================================================================
"""
功能：批量转换整本书的所有章节

代码：
    from tts.audio_converter import AudioConverter

    # 创建转换器
    converter = AudioConverter(voice="zh-CN-XiaoxiaoNeural")

    # 转换整本书
    chapter_dir = "chapter/三体(全三册)"
    output_dir = "audios"
    book_name = "三体(全三册)"

    saved_files = converter.convert_book(chapter_dir, output_dir, book_name)

    print(f"成功转换 {len(saved_files)} 个章节")

预期输出：
    成功转换 98 个章节
"""


# ============================================================================
# 示例5: 使用 ChatTTS 转换（需要安装 ChatTTS）
# ============================================================================
"""
功能：使用 ChatTTS 进行离线语音转换

前置条件：
    pip install ChatTTS torch torchaudio

代码：
    from chat_tts_converter import ChatTTSConverter

    # 检查 ChatTTS 是否可用
    if not ChatTTSConverter.is_available():
        print("请先安装 ChatTTS: pip install ChatTTS torch torchaudio")
        exit(1)

    # 创建转换器（自动检测 GPU）
    converter = ChatTTSConverter(use_gpu=True)

    # 加载模型（首次使用会下载模型）
    if not converter.load_model():
        print("模型加载失败")
        exit(1)

    # 转换文本
    text = "你好，这是一个测试。欢迎使用 ChatTTS 语音合成系统。"
    output_path = "test_output.wav"

    success = converter.text_to_speech(text, output_path)

    if success:
        print(f"转换成功: {output_path}")

预期输出：
    正在加载ChatTTS模型...
    ChatTTS模型加载成功
    文本已分为 1 段
    转换第 1/1 段 (30 字符)...
    音频保存成功: test_output.wav
    转换成功: test_output.wav
"""


# ============================================================================
# 示例6: 选择不同的语音
# ============================================================================
"""
功能：使用不同的语音进行转换

代码：
    from tts.audio_converter import AudioConverter

    # 可用的中文语音
    voices = [
        "zh-CN-XiaoxiaoNeural",   # 女声，自然流畅
        "zh-CN-YunyangNeural",    # 男声，新闻播报风格
        "zh-CN-YunxiNeural",      # 男声，年轻活泼
        "zh-CN-XiaoyiNeural",     # 女声，温柔甜美
    ]

    # 使用男声转换
    converter = AudioConverter(voice="zh-CN-YunyangNeural")

    converter.convert_chapter(
        "chapter/三体(全三册)/chapter1.md",
        "audios/三体(全三册)/chapter1_male.mp3"
    )

预期输出：
    使用男声（新闻播报风格）生成的音频文件
"""


# ============================================================================
# 示例7: 完整流程（提取 + 转换）
# ============================================================================
"""
功能：执行完整的提取和转换流程

代码：
    import shutil
    from mobi_handler.mobi_extractor import process_mobi
    from tts.audio_converter import AudioConverter

    # 配置
    mobi_path = "books/三体(全三册).mobi"
    chapter_dir = "chapter"
    audio_dir = "audios"
    voice = "zh-CN-XiaoxiaoNeural"

    # 步骤1: 提取章节
    print("步骤1: 提取章节...")
    saved_files, tempdir = process_mobi(mobi_path, chapter_dir)
    print(f"提取了 {len(saved_files)} 个章节")
    shutil.rmtree(tempdir, ignore_errors=True)

    # 步骤2: 转换音频
    print("\\n步骤2: 转换音频...")
    converter = AudioConverter(voice=voice)

    book_name = Path(mobi_path).stem
    audio_files = converter.convert_book(
        f"{chapter_dir}/{book_name}",
        audio_dir,
        book_name
    )

    print(f"\\n完成！成功转换 {len(audio_files)} 个章节")

预期输出：
    步骤1: 提取章节...
    提取了 98 个章节

    步骤2: 转换音频...
    处理 1/98: chapter1.md
    处理 2/98: chapter2.md
    ...

    完成！成功转换 98 个章节
"""


# ============================================================================
# 示例8: 自定义配置
# ============================================================================
"""
功能：使用自定义配置

代码：
    from config import (
        PROJECT_ROOT,
        BOOKS_DIR,
        CHAPTER_DIR,
        AUDIOS_DIR,
        AUDIO_FORMAT,
        ensure_dirs
    )

    # 确保目录存在
    ensure_dirs()

    # 使用配置
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"书籍目录: {BOOKS_DIR}")
    print(f"章节目录: {CHAPTER_DIR}")
    print(f"音频目录: {AUDIOS_DIR}")
    print(f"音频格式: {AUDIO_FORMAT}")

预期输出：
    项目根目录: D:\CODE\voicebook
    书籍目录: D:\CODE\voicebook\books
    章节目录: D:\CODE\voicebook\chapter
    音频目录: D:\CODE\voicebook\audios
    音频格式: mp3
"""


# ============================================================================
# 示例9: 错误处理示例
# ============================================================================
"""
功能：展示如何处理可能出现的错误

代码：
    from mobi_handler.mobi_extractor import process_mobi
    from tts.audio_converter import AudioConverter
    import shutil

    try:
        # 尝试提取
        saved_files, tempdir = process_mobi("nonexistent.mobi", "chapter")
    except FileNotFoundError as e:
        print(f"文件不存在: {e}")
    except Exception as e:
        print(f"提取失败: {e}")
    else:
        shutil.rmtree(tempdir, ignore_errors=True)

    try:
        # 尝试转换
        converter = AudioConverter()
        success = converter.convert_chapter(
            "nonexistent.md",
            "output.mp3"
        )
        if not success:
            print("转换失败")
    except Exception as e:
        print(f"转换出错: {e}")

预期输出：
    文件不存在: [Errno 2] No such file or directory: 'nonexistent.mobi'
"""


# ============================================================================
# 示例10: 批量处理多本书
# ============================================================================
"""
功能：批量处理多本 MOBI 书籍

代码：
    import shutil
    from pathlib import Path
    from mobi_handler.mobi_extractor import process_mobi
    from tts.audio_converter import AudioConverter

    # 获取所有 MOBI 文件
    books_dir = Path("books")
    mobi_files = list(books_dir.glob("*.mobi"))

    print(f"找到 {len(mobi_files)} 本书籍")

    converter = AudioConverter()

    for mobi_file in mobi_files:
        print(f"\\n处理: {mobi_file.name}")

        # 提取章节
        saved_files, tempdir = process_mobi(
            str(mobi_file),
            "chapter"
        )
        shutil.rmtree(tempdir, ignore_errors=True)

        # 转换音频
        book_name = mobi_file.stem
        audio_files = converter.convert_book(
            f"chapter/{book_name}",
            "audios",
            book_name
        )

        print(f"完成: {len(audio_files)} 个章节")

预期输出：
    找到 2 本书籍

    处理: 三体(全三册).mobi
    完成: 98 个章节

    处理: 其他书籍.mobi
    完成: XX 个章节
"""


# ============================================================================
# 示例11: 启动 GUI 界面
# ============================================================================
"""
功能：启动图形化界面

代码：
    from gui import run_gui

    # 启动 GUI
    run_gui()

或者：
    python -m src.gui

预期输出：
    打开图形化界面窗口
"""


# ============================================================================
# 示例12: 使用命令行工具
# ============================================================================
"""
功能：通过命令行使用 VoiceBook

命令：
    # 查看帮助
    python -m src.main --help

    # 提取章节
    python -m src.main extract books/三体(全三册).mobi

    # 转换音频
    python -m src.main convert chapter/三体(全三册) -v zh-CN-YunyangNeural

    # 完整流程
    python -m src.main process books/三体(全三册).mobi

    # 列出语音
    python -m src.main voices

预期输出：
    根据命令执行相应操作
"""


if __name__ == "__main__":
    print("VoiceBook 使用示例集")
    print("=" * 50)
    print("\n本文件包含 12 个使用示例，请查看源代码了解详情。")
    print("\n示例列表：")
    print("  1. 基本 MOBI 提取")
    print("  2. 提取并指定输出目录")
    print("  3. 使用 Edge-TTS 转换单个章节")
    print("  4. 使用 Edge-TTS 转换整本书")
    print("  5. 使用 ChatTTS 转换")
    print("  6. 选择不同的语音")
    print("  7. 完整流程（提取 + 转换）")
    print("  8. 自定义配置")
    print("  9. 错误处理示例")
    print("  10. 批量处理多本书")
    print("  11. 启动 GUI 界面")
    print("  12. 使用命令行工具")
