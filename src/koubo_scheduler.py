r"""口播一条龙任务清单生成器 - 将koubo.md技能逻辑固化为脚本。

用法：
    python -m src.koubo_scheduler -i 5 -t 原理6-10 \
        -a "chapter\游戏设计的100个原理\chapter12.md,chapter\游戏设计的100个原理\chapter13.md"
"""

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CHAPTER_DIR = PROJECT_ROOT / "chapter"

# 中文数字映射（支持1-99）
_DIGITS = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
_TENS = ["", "十", "二十", "三十", "四十", "五十", "六十", "七十", "八十", "九十"]


def num_to_chinese(n: int) -> str:
    """将阿拉伯数字转为中文数字，如 1→一, 10→十, 23→二十三"""
    if not 1 <= n <= 99:
        return str(n)
    tens = n // 10
    ones = n % 10
    if tens == 0:
        return _DIGITS[ones]
    if tens == 1 and ones == 0:
        return "十"
    if tens == 1:
        return f"十{_DIGITS[ones]}"
    if ones == 0:
        return _TENS[tens]
    return f"{_TENS[tens]}{_DIGITS[ones]}"


def derive_book_name(article_paths: list[Path]) -> str:
    """从文章路径推导书名（chapter/书名的第一级目录）。"""
    for ap in article_paths:
        try:
            rel = ap.relative_to(CHAPTER_DIR)
            return rel.parts[0]
        except ValueError:
            # 尝试从路径名中提取
            parts = ap.parts
            if "chapter" in parts:
                idx = list(parts).index("chapter")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    return "未知书籍"


def build_content(issue: int, topic: str, article_paths: list[str]) -> tuple[str, Path, Path, Path, Path]:
    """构建任务清单内容，返回 (content, task_path, distill_path, shownotes_path, audio_path)。"""
    articles = [Path(p.strip()) for p in article_paths if p.strip()]
    if not articles:
        raise ValueError("关联文章列表为空")

    book_name = derive_book_name(articles)
    issue_cn = num_to_chinese(issue)

    output_dir = PROJECT_ROOT / "project" / book_name / f"第{issue_cn}期"
    distill_path = output_dir / f"{topic}-distill.md"
    shownotes_path = output_dir / f"{topic}-shownotes.md"
    audio_path = output_dir / f"{topic}-audio.mp3"
    task_path = output_dir / f"{topic}-task.md"

    # 关联文章简写使用相对路径格式
    article_brief = f"{articles[0]} - {articles[-1]}"

    # 路径统一转为相对于项目根目录的形式
    def rel_path(p: Path) -> str:
        try:
            return str(p.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(p)

    content = f"""# 第{issue}期：{topic}

* 期数: 第{issue}期
* 主题名：{topic}
* 标题：{book_name} - {topic}
* 关联文章内容: {article_brief}
* 输出口播稿路径：{rel_path(distill_path)}
* 输出音频路径：{rel_path(audio_path)}
* 输出shownotes路径：{rel_path(shownotes_path)}

[ ] 生成口播稿：使用 book-distill 技能，对 {article_brief} 进行阅读整理内容，生成一份说书口稿，口稿文件输出到 {rel_path(distill_path)} 中
[ ] 生成shownotes：使用 show-notes 技能，对 {rel_path(distill_path)} 进行阅读生成shownotes 输出到 {rel_path(shownotes_path)} 中
[ ] 校准时长：使用 note_time_verify 技能校准 {rel_path(distill_path)} 的总时长和 {rel_path(shownotes_path)} 的时间戳
[ ] ⚠️ 人工审核：请务必在上一步全部完成后仔细review口播稿和shownotes内容，确认无误后再继续。千万不要跳过审核直接生成音频！
[ ] 生成口播音频：使用 audio_by_doubao 技能为 {rel_path(distill_path)} 文档生成口播音频到 {rel_path(audio_path)} 路径下
"""
    return content, task_path, distill_path, shownotes_path, audio_path


def generate(issue: int, topic: str, article_paths: list[str]) -> str:
    """生成本期任务清单文件，返回任务清单文件路径。"""
    content, task_path, _, _, _ = build_content(issue, topic, article_paths)
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(content, encoding="utf-8")
    return str(task_path)


def main():
    parser = argparse.ArgumentParser(
        description="口播一条龙任务清单生成器",
    )
    parser.add_argument(
        "-i", "--issue", type=int, required=True,
        help="期数（阿拉伯数字），如 5",
    )
    parser.add_argument(
        "-t", "--topic", type=str, required=True,
        help='主题名，如 原理6-10',
    )
    parser.add_argument(
        "-a", "--articles", type=str, required=True,
        help="关联文章路径，逗号分隔",
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true",
        help="仅打印任务清单内容，不写入文件",
    )

    args = parser.parse_args()
    article_list = [a.strip() for a in args.articles.split(",") if a.strip()]

    if args.dry_run:
        content, *_ = build_content(args.issue, args.topic, article_list)
        print(content)
    else:
        task_path = generate(args.issue, args.topic, article_list)
        print(f"任务清单已生成：{task_path}")


if __name__ == "__main__":
    main()
