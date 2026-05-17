"""
合成 原理1-5.md 为音频（Edge-TTS, 成熟女声）
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tts.tts_engine import TTSEngine

project_root = Path(__file__).parent.parent
input_path = project_root / "project" / "游戏设计的100个原理" / "原理1-5.md"
output_dir = project_root / "audios" / "游戏设计的100个原理"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "原理1-5.mp3"

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

print(f"文本长度: {len(text)} 字符")
print()

# 列出所有可用 Edge TTS 中文女声
async def find_female_voices():
    voices = await TTSEngine.get_all_voices_async()
    zh_female = [v for v in voices
                 if v.get("Locale", "").startswith("zh-CN")
                 and v.get("Gender") == "Female"]
    print("Edge TTS 可用中文女声:")
    for v in zh_female:
        friendly = v.get("FriendlyName", v.get("ShortName", ""))
        print(f"  {v['ShortName']} - {friendly}")
    return [v["ShortName"] for v in zh_female]

female_voices = asyncio.run(find_female_voices())

# 选最接近成熟女声的：xiaoxiao 自然流畅，或 yunyang 风格的对应女声
# Edge TTS 中 xiaoxiao 是较自然的通用女声
voice = "zh-CN-XiaoxiaoNeural"
if "zh-CN-XiaohanNeural" in female_voices:
    voice = "zh-CN-XiaohanNeural"  # 晓涵 - 更沉稳温柔
elif "zh-CN-XiaoxiaoNeural" in female_voices:
    voice = "zh-CN-XiaoxiaoNeural"

print(f"\n选用音色: {voice}")
print(f"输出路径: {output_path}")
print(f"开始合成...")

# 跳过 TTSEngine 的有限白名单，直接用 edge_tts Communicate
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "libs"))
from edge_tts import Communicate

async def synthesize():
    communicate = Communicate(text, voice)
    await communicate.save(str(output_path))
    return True

success = asyncio.run(synthesize())

if success:
    file_size = output_path.stat().st_size / 1024 / 1024
    print(f"合成成功! 文件大小: {file_size:.2f} MB")
    print(f"输出: {output_path}")
    print(f"使用音色: {voice}")
else:
    print("合成失败!")
    sys.exit(1)
