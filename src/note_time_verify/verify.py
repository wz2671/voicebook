"""note_time_verify — 讲稿时长校准工具

根据口播稿字符数和实际音频语速系数，计算总时长和分段 timecode，
用于校准 distill 总时长声明和 shownotes 时间戳。

用法:
    python -m src.note_time_verify.verify <口播稿路径> [--shownotes]

输出:
    - 总字符数、估算总时长
    - 各原理分段时间戳
    - 可直接用于 shownotes 的 timecode 列表（--shownotes）
"""

import re
import sys
from pathlib import Path

# 语速系数 (chars/min)，基于第五期实际音频 16:43 校准
RATE = 312

# === 分段检测 ===

# 原理章节开头：先进入/接下来是/然后是/最后，+ 原理N + 名称
_SECTION_RE = re.compile(
    r'(?:先进入|好，接下来是|接下来是|然后是|最后，)'
    r'原理[一二三四五六七八九十百千]+'
    r'(?:[，,][^。\n]{0,40})?'
)

# 回顾总结开头
_REVIEW_RE = re.compile(
    r'(?:好，)?[^。\n]{0,10}(?:原理|个原理)[^。]{0,10}(?:讲完|回顾|总结)'
)


# shownotes 标签清理：去掉口语过渡前缀
_CLEAN_PREFIXES = [
    ('好，接下来是', ''),
    ('接下来是', ''),
    ('先进入', ''),
    ('然后是', ''),
    ('最后，', ''),
]

# 中文数字 → 阿拉伯数字
_CN_DIGIT = dict(zip('一二三四五六七八九', range(1, 10)))
_CN_UNIT = {'十': 10, '百': 100}


def _cn_to_int(s: str) -> int:
    """中文数字 → int，如 二十一 → 21, 一百 → 100"""
    result = 0
    cur = 0  # 当前累积的数字位
    for ch in s:
        if ch in _CN_DIGIT:
            cur = _CN_DIGIT[ch]
        elif ch in _CN_UNIT:
            unit = _CN_UNIT[ch]
            cur = (cur or 1) * unit
            result += cur
            cur = 0
    result += cur
    return result


def _clean_label(text: str) -> str:
    """清理标签，去掉口语过渡词，规范为 shownotes 格式

    '先进入原理二十一，解谜游戏的设计' → '原理21 — 解谜游戏的设计'
    '好，五个原理都讲完了，我们来简单回顾一下' → '回顾总结'
    """
    text = text.strip()

    # 回顾总结 → 固定标签
    if '回顾' in text or '总结' in text or '讲完' in text:
        return '回顾总结'

    # 清理前缀
    for prefix, _ in _CLEAN_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    # 中文数字 → 阿拉伯数字：原理二十一 → 原理21
    m_cn = re.search(r'原理([一二三四五六七八九十百]+)', text)
    if m_cn:
        cn = m_cn.group(1)
        num = _cn_to_int(cn)
        text = text.replace(f'原理{cn}', f'原理{num}')

    # 逗号替换为 shownotes 的分隔符
    text = text.replace('，', ' — ', 1)
    text = text.replace(',', ' — ', 1)

    return text.strip().rstrip('— ')


def detect_sections(content: str) -> list[tuple[str, str]]:
    """从口播稿中检测分段时间点，返回 [(timecode_str, label), ...]"""
    total = len(content)
    sections = []

    # 找所有原理章节开头
    for m in _SECTION_RE.finditer(content):
        label = _clean_label(m.group())
        sections.append((m.start(), label))

    # 找回顾总结开头
    m_review = _REVIEW_RE.search(content)
    if m_review:
        label = _clean_label(m_review.group())
        sections.append((m_review.start(), label))

    # 按位置排序
    sections.sort(key=lambda x: x[0])

    # 计算时间戳
    result = []
    for pos, label in sections:
        ts_minutes = (pos / total) * (total / RATE)
        m, s = divmod(int(ts_minutes * 60), 60)
        result.append((f"{m:02d}:{s:02d}", label))

    return result


def format_duration(seconds_total: float) -> str:
    """总秒数 → 可读时长，如 '16分43秒（约十六分半）'"""
    m, s = divmod(int(seconds_total), 60)
    half = "半" if 25 <= s < 45 else ""
    mm = m + 1 if s >= 45 else m
    if half:
        return f"{m}分{s}秒（约{m}分{half}）"
    elif s >= 45:
        return f"{m}分{s}秒（约{mm}分钟）"
    elif s < 3:
        return f"{m}分{s}秒（约{m}分钟）"
    else:
        return f"{m}分{s}秒"


# === 主入口 ===

def verify(filepath: str, shownotes: bool = False) -> dict:
    """分析口播稿，返回时长信息

    Returns:
        dict with keys: filepath, total_chars, duration_min, duration_str,
                        sections, shownotes_lines
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    content = path.read_text(encoding="utf-8")
    total = len(content)
    duration_min = total / RATE
    duration_sec = duration_min * 60

    sections = detect_sections(content)

    # 生成 shownotes 时间戳行
    shownotes_lines = []
    if shownotes and sections:
        shownotes_lines = [
            f"{ts} {label}" for ts, label in sections
        ]

    return {
        "filepath": str(path),
        "total_chars": total,
        "duration_min": duration_min,
        "duration_str": format_duration(duration_sec),
        "sections": sections,
        "shownotes_lines": shownotes_lines,
    }


def print_report(result: dict, shownotes: bool = False) -> None:
    """格式化打印校准报告"""
    print(f"文件: {result['filepath']}")
    print(f"总字符数: {result['total_chars']}")
    print(f"估算总时长: {result['duration_str']}")
    print()

    if result["sections"]:
        print("分段时间戳:")
        for ts, label in result["sections"]:
            print(f"  {ts}  {label}")
        print()

    print("可用于校准:")
    print(f"  口播稿: 本期时长大约{result['duration_str'].split('（')[-1].rstrip(')')}")
    print(f"  shownotes: 替换时间戳列表即可")

    if shownotes and result["shownotes_lines"]:
        print()
        print("shownotes 时间戳 (可直接复制):")
        for line in result["shownotes_lines"]:
            print(f"  {line}")


def main():
    if len(sys.argv) < 2:
        print("用法: python -m src.note_time_verify.verify <口播稿路径> [--shownotes]")
        sys.exit(1)

    filepath = sys.argv[1]
    show_shownotes = "--shownotes" in sys.argv

    try:
        result = verify(filepath, shownotes=show_shownotes)
        print_report(result, shownotes=show_shownotes)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
