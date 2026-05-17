---
name: audio_by_doubao
description: 使用豆包 TTS 将 .md 文档生成音频，默认使用 vv 活泼女声
---

# audio_by_doubao — 豆包 TTS 音频生成

当用户指定一个或多个 .md 文档路径时，使用豆包（火山引擎）TTS 引擎生成对应的 MP3 音频文件。

## 默认参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 引擎 | `doubao` | 豆包 TTS (火山引擎异步长文本 API v3) |
| 发音人 | `zh_female_vv_uranus_bigtts` | vv 活泼灵动女声（默认） |
| 模型 | `seed-tts-2.0` | 豆包语音合成大模型 2.0 |
| 输出格式 | `mp3` | 在 `.env.local` 中配置 |

用户可以通过命令行指定不同的发音人，例如使用知性成熟女声：
```
python -m src.main convert <路径> --engine doubao -v ICL_zh_female_chengshu_v1_tob
```

## 可用音色

执行 `python -m src.main voices` 可查看所有引擎的可用音色列表。

豆包 seed-tts-2.0 中文女声：
- `zh_female_vv_uranus_bigtts` — 活泼灵动（默认）
- `zh_female_xiaohe_jupiter_bigtts` — 甜美活泼（台湾口音）
- `zh_female_xueayi_saturn_bigtts` — 儿童绘本

豆包 seed-tts-2.0 中文男声：
- `zh_male_yunzhou_jupiter_bigtts` — 清爽沉稳
- `zh_male_xiaotian_jupiter_bigtts` — 清爽磁性

## 执行流程

1. 确认用户提供的文件路径存在且为 `.md` 文件
2. 如果用户未指定发音人，使用默认 `zh_female_vv_uranus_bigtts`
3. 执行转换命令：
   ```bash
   python -m src.main convert "<文件或目录路径>" --engine doubao -v <发音人>
   ```
4. 向用户报告生成结果（输出路径、耗时、成功/失败状态）

## 支持的输入方式

- **单个文件**: `python -m src.main convert "project/xxx/doc.md" --engine doubao`
- **整个目录**: `python -m src.main convert "chapter/书名" --engine doubao`
- **自定义发音人**: `python -m src.main convert "path" --engine doubao -v <speaker>`

## 示例

用户说：
```
使用豆包生成 project/游戏设计的100个原理/原理1-5.md 的音频
```

或：
```
/audio_by_doubao project/游戏设计的100个原理/原理1-5.md
```

执行：
```bash
cd <项目根目录> && python -m src.main convert "<路径>" --engine doubao -v zh_female_vv_uranus_bigtts
```

## 注意事项

- 文件编码必须是 UTF-8
- 单次最大支持 10 万字符
- 音频输出到 `audios/<父目录名>/<文件名>.mp3`
- 合成耗时与文本长度成正比（约 1-5 分钟/章）
- 音频在服务端保存 7 天，下载链接有效期 1 小时
- 需要 `.env.local` 中配置有效的 `DOUBAO_APP_ID` 和 `DOUBAO_ACCESS_KEY`
