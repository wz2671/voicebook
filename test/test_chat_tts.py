"""
ChatTTS 功能测试脚本

测试使用 chapter/三体(全三册)/ 目录下的 markdown 文件
输出目录为 audios/三体(全三册)_chat/
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "libs"))

from src.tts.chat_tts_converter import ChatTTSConverter


def test_chat_tts_availability():
    print("=" * 60)
    print("测试 1: 检查 ChatTTS 可用性")
    print("=" * 60)
    
    available = ChatTTSConverter.is_available()
    print(f"ChatTTS 可用: {available}")
    
    if not available:
        print("\n错误: ChatTTS 不可用")
        print("请确保已安装所需依赖:")
        print("  pip install torch torchaudio")
        return False
    
    print("✓ ChatTTS 可用性检查通过")
    return True


def test_text_to_speech():
    print("\n" + "=" * 60)
    print("测试 2: 基本文本转语音功能")
    print("=" * 60)
    
    converter = ChatTTSConverter(use_gpu=True)
    
    test_text = "你好，这是一个测试。欢迎使用ChatTTS语音合成系统。"
    output_dir = project_root / "audios" / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test_basic.wav"
    
    print(f"测试文本: {test_text}")
    print(f"输出文件: {output_file}")
    
    success = converter.text_to_speech(test_text, str(output_file))
    
    if success and output_file.exists():
        file_size = output_file.stat().st_size
        print(f"✓ 基本文本转语音测试通过")
        print(f"  文件大小: {file_size / 1024:.2f} KB")
        return True
    else:
        print("✗ 基本文本转语音测试失败")
        return False


def test_chapter_conversion():
    print("\n" + "=" * 60)
    print("测试 3: 章节文件转换功能")
    print("=" * 60)
    
    chapter_dir = project_root / "chapter" / "三体(全三册)"
    output_dir = project_root / "audios" / "三体(全三册)_chat"
    
    if not chapter_dir.exists():
        print(f"✗ 章节目录不存在: {chapter_dir}")
        return False
    
    md_files = sorted(chapter_dir.glob("chapter*.md"))
    if not md_files:
        print(f"✗ 未找到章节文件")
        return False
    
    print(f"章节目录: {chapter_dir}")
    print(f"输出目录: {output_dir}")
    print(f"找到 {len(md_files)} 个章节文件")
    
    converter = ChatTTSConverter(use_gpu=True)
    
    test_files = md_files[:3]
    print(f"\n测试前 {len(test_files)} 个章节...")
    
    success_count = 0
    for i, md_file in enumerate(test_files, 1):
        print(f"\n处理第 {i}/{len(test_files)} 个: {md_file.name}")
        
        output_file = output_dir / md_file.name.replace('.md', '.wav')
        
        if converter.convert_chapter(str(md_file), str(output_file)):
            if output_file.exists():
                file_size = output_file.stat().st_size
                print(f"  ✓ 成功: {output_file.name} ({file_size / 1024:.2f} KB)")
                success_count += 1
            else:
                print(f"  ✗ 文件未生成")
        else:
            print(f"  ✗ 转换失败")
    
    if success_count == len(test_files):
        print(f"\n✓ 章节转换测试通过 ({success_count}/{len(test_files)})")
        return True
    else:
        print(f"\n✗ 章节转换测试部分失败 ({success_count}/{len(test_files)})")
        return False


def test_long_text_split():
    print("\n" + "=" * 60)
    print("测试 4: 长文本分段功能")
    print("=" * 60)
    
    converter = ChatTTSConverter(use_gpu=True)
    
    long_text = """
    这是一段很长的测试文本。我们需要验证系统能够正确地将长文本分割成多个段落。
    每个段落应该尽量在句子边界处分割。这样可以保证语音合成的连贯性。
    系统应该能够处理各种标点符号，包括句号、问号、感叹号等。
    让我们看看分段效果如何。
    """ * 5
    
    segments = converter.split_text(long_text.strip(), max_length=200)
    
    print(f"原始文本长度: {len(long_text)} 字符")
    print(f"分段数量: {len(segments)}")
    
    for i, seg in enumerate(segments[:5], 1):
        print(f"  段 {i}: {len(seg)} 字符 - {seg[:30]}...")
    
    if len(segments) > 1:
        print(f"\n✓ 长文本分段测试通过")
        return True
    else:
        print(f"\n✗ 长文本分段测试失败")
        return False


def run_all_tests():
    print("\n" + "=" * 60)
    print("ChatTTS 功能测试套件")
    print("=" * 60)
    
    results = []
    
    results.append(("可用性检查", test_chat_tts_availability()))
    
    if results[0][1]:
        results.append(("基本文本转语音", test_text_to_speech()))
        results.append(("长文本分段", test_long_text_split()))
        results.append(("章节文件转换", test_chapter_conversion()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
