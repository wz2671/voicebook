---
name: note_time_verify
description: 校准口播稿时长。输入 distill 文件，自动计算总时长和各段时间戳，用于修正 shownotes 时间码和 distill 时长声明。
---

# note_time_verify — 讲稿时长校准

你是一个播客时长校准助手。给定一份口播 distill 稿，自动计算总时长和分段时间戳，输出可直接用于修正 distill 和 shownotes 的结果。

## 输入

用户指定一个 distill 口播稿路径，例如：

```
校准 project/游戏设计的100个原理/第五期/原理21-25-distill.md
```

## 执行流程

运行脚本：

```bash
cd <项目根目录> && python -m src.note_time_verify.verify "<distill稿路径>" --shownotes
```

## 输出解读

脚本会输出：

| 输出项 | 用途 |
|--------|------|
| 总字符数、估算总时长 | 修正 distill 第 6 行 `本期时长大约XX分钟` |
| 分段时间戳 | 修正 shownotes 中的时间戳列表 |

## 校准操作

拿到输出后，执行两个修正：

1. **distill 时长** — 找到文件中的 `本期时长大约` 行，替换为输出提示的时长
2. **shownotes 时间戳** — 打开对应的 shownotes 文件，用输出的时间戳列表替换原有时间戳行

## 技术细节

- 语速系数 `RATE = 312`（chars/min），基于第五期实际音频 16:43 校准
- 分段检测基于 distill 模板的口语过渡模式（`先进入原理`、`接下来是原理`、`最后，原理`、回顾总结标记）
- 时间戳按字符位置占总字符数的比例分配，假设朗读速度均匀
