r"""批量生成《游戏设计的100个原理》所有期待办清单。

原理→章节对应关系（每期5个原理，章节 = 原理编号 + 6，跳过篇头章节36、69、88）：

已验证：章节标题中的原理编号与预期一致。
- 原理26→chapter32, ..., 原理29→chapter35, 原理30→chapter37（跳过chapter36篇头）
- 原理61→chapter68, 原理62→chapter70（跳过chapter69篇头）
- 原理79→chapter87, 原理80→chapter89（跳过chapter88篇头）
- 原理100→chapter109（最后）

用法：先 dry_run=True 检查命令，确认后改 dry_run=False 执行。
"""

import subprocess
import sys

# 每期：(期数, 原理起始, 原理结束, [章节编号列表])
ISSUES = [
    # 已有: 第一~五期 (原理1-25)，此处从第六期开始
    (6,  26, 30, [32, 33, 34, 35, 37]),        # 跳36(篇头)
    (7,  31, 35, [38, 39, 40, 41, 42]),
    (8,  36, 40, [43, 44, 45, 46, 47]),
    (9,  41, 45, [48, 49, 50, 51, 52]),
    (10, 46, 50, [53, 54, 55, 56, 57]),
    (11, 51, 55, [58, 59, 60, 61, 62]),
    (12, 56, 60, [63, 64, 65, 66, 67]),
    (13, 61, 65, [68, 70, 71, 72, 73]),        # 跳69(篇头)
    (14, 66, 70, [74, 75, 76, 77, 78]),
    (15, 71, 75, [79, 80, 81, 82, 83]),
    (16, 76, 80, [84, 85, 86, 87, 89]),        # 跳88(篇头)
    (17, 81, 85, [90, 91, 92, 93, 94]),
    (18, 86, 90, [95, 96, 97, 98, 99]),
    (19, 91, 95, [100, 101, 102, 103, 104]),
    (20, 96, 100, [105, 106, 107, 108, 109]),
]

BOOK = "游戏设计的100个原理"
dry_run = False  # 改为 False 后执行


def build_command(issue: int, start: int, end: int, chapters: list[int]) -> str:
    """构建 koubo_scheduler 命令行。"""
    topic = f"原理{start}-{end}"
    article_paths = ", ".join(
        f"chapter\\{BOOK}\\chapter{c}.md" for c in chapters
    )
    if dry_run:
        return (
            f"python -m src.koubo_scheduler -i {issue} "
            f'-t "{topic}" '
            f'-a "{article_paths}" '
            f"--dry-run"
        )
    else:
        return (
            f"python -m src.koubo_scheduler -i {issue} "
            f'-t "{topic}" '
            f'-a "{article_paths}"'
        )


def main():
    print("=" * 60)
    print("《游戏设计的100个原理》待办清单批量生成")
    print(f"模式: {'DRY RUN (仅预览)' if dry_run else '执行写入'}")
    print(f"共 {len(ISSUES)} 期 (第六期 ~ 第二十期)")
    print("=" * 60)

    for issue, start, end, chapters in ISSUES:
        cmd = build_command(issue, start, end, chapters)
        print(f"\n# 第{issue}期：原理{start}-{end}")
        print(f"# 章节: {chapters}")
        print(cmd)
        if not dry_run:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(f"[错误] {result.stderr}", file=sys.stderr)

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN 完成。确认无误后，将 dry_run 改为 False 执行。")
    else:
        print("全部任务清单已生成。")


if __name__ == "__main__":
    main()
