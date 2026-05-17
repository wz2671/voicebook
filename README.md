# VoiceBook — 电子书转音频工具

将 MOBI 电子书自动转换为有声书，支持多种 TTS 引擎。

## 功能

- **MOBI 文字提取** — 解析 MOBI 电子书，按章节分割输出 Markdown 文件
- **文字转语音** — 三套 TTS 引擎可选，生成 MP3/WAV 音频
- **图形化界面** — tkinter GUI，操作简便
- **命令行工具** — 支持脚本化和批量处理

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 完整流程：提取 + 转换（使用免费 Edge-TTS）
python -m src.main process books/mybook.mobi

# 查看所有命令
python -m src.main --help

# 启动图形界面
python run_gui.py
```

## TTS 引擎对比

| 引擎 | 类型 | 质量 | 速度 | 网络 | 费用 |
|------|------|------|------|------|------|
| Edge-TTS | 微软云端 | 优秀 | 快 | 需要 | 免费 |
| Minimax | API 云端 | 优秀 | 快 | 需要 | 付费 |
| ChatTTS | 本地模型 | 良好 | 慢 | 离线 | 免费 |

Minimax 需要在 `.env.local` 中配置 API Key（前往 [platform.minimax.io](https://platform.minimax.io) 获取）。

ChatTTS 需要额外安装并下载约 2GB 模型：

```bash
pip install ChatTTS torch torchaudio
```

## 命令行用法

```bash
# 提取章节（MOBI → Markdown）
python -m src.main extract books/mybook.mobi
python -m src.main extract books/mybook.mobi -o ./output

# 转换音频（Markdown → MP3）
python -m src.main convert chapter/mybook
python -m src.main convert chapter/mybook --engine chat-tts
python -m src.main convert chapter/mybook --engine minimax -v female-shaonv

# 完整流程（提取 + 转换）
python -m src.main process books/mybook.mobi --engine minimax

# 列出可用语音
python -m src.main voices
```

## 配置（.env.local）

在项目根目录创建 `.env.local` 文件（已 gitignore）：

```ini
# Edge-TTS（默认引擎，免费）
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural

# Minimax API
MINIMAX_API_KEY=your_api_key
MINIMAX_VOICE_ID=female-shaonv

# ChatTTS
CHAT_TTS_USE_GPU=true

# 通用
AUDIO_FORMAT=mp3
```

## 项目结构

```
voicebook/
├── books/              # 输入：MOBI 文件
├── chapter/            # 输出：章节 Markdown
├── audios/             # 输出：音频文件
├── src/
│   ├── main.py         # CLI 入口
│   ├── config.py       # 路径配置
│   ├── env.py          # 环境变量配置中心
│   ├── mobi_handler/   # MOBI 提取
│   ├── tts/            # TTS 引擎
│   ├── gui/            # GUI 界面
│   └── libs/           # 内置第三方库
└── test/               # 测试脚本
```

## 环境要求

- Python 3.8+
- ffmpeg（音频合并，可选）
- ChatTTS 需要 4GB+ 显存（GPU）或 8GB+ 内存（CPU）
