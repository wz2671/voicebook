# VoiceBook 使用指引

## 简介

VoiceBook 是一个本地电子书转音频工具，可以将 MOBI 格式的电子书转换为音频文件。主要功能包括：

- **MOBI 文字提取**：从 MOBI 文件中提取文字内容，按章节分割输出为 Markdown 文件
- **文字转语音**：支持多种 TTS 引擎，将文字转换为高质量的中文语音
- **图形化界面**：提供直观的 GUI 界面，无需命令行操作

### 支持的格式

| 输入格式 | 输出格式 |
|---------|---------|
| MOBI | Markdown (.md) |
| Markdown (.md) | MP3 / WAV |

---

## 安装

### 系统要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

### 基础安装

```bash
# 克隆或下载项目
cd voicebook

# 安装基础依赖
pip install -r requirements.txt
```

### 可选依赖

**ChatTTS（离线高质量语音）**：
```bash
pip install ChatTTS torch torchaudio
```

> 注意：ChatTTS 需要下载约 2GB 的模型文件，首次使用会自动下载。

---

## 命令行版本

### 基本命令

```bash
python -m src.main <command> [options]
```

### 命令列表

| 命令 | 说明 |
|------|------|
| `extract` | 从 MOBI 文件提取章节 |
| `convert` | 将章节转换为音频 |
| `process` | 完整流程（提取 + 转换） |
| `voices` | 列出可用的 TTS 语音 |

### extract - 提取章节

从 MOBI 文件中提取文字内容，按章节分割输出。

```bash
# 基本用法
python -m src.main extract books/三体(全三册).mobi

# 指定输出目录
python -m src.main extract books/三体(全三册).mobi -o ./output

# 显示详细日志
python -m src.main extract books/三体(全三册).mobi -V
```

**参数说明**：
- `mobi_file`：MOBI 文件路径
- `-o, --output`：输出目录（默认：chapter/）
- `-V, --verbose`：显示详细日志

### convert - 转换音频

将章节 Markdown 文件转换为音频。

```bash
# 基本用法
python -m src.main convert chapter/三体(全三册)

# 指定语音
python -m src.main convert chapter/三体(全三册) -v zh-CN-YunyangNeural

# 指定输出目录
python -m src.main convert chapter/三体(全三册) -o ./audio_output
```

**参数说明**：
- `chapter_dir`：章节目录路径
- `-o, --output`：输出目录（默认：audios/）
- `-v, --voice`：语音名称（默认：zh-CN-XiaoxiaoNeural）
- `-V, --verbose`：显示详细日志

### process - 完整流程

执行提取和转换的完整流程。

```bash
# 基本用法
python -m src.main process books/三体(全三册).mobi

# 指定语音
python -m src.main process books/三体(全三册).mobi -v zh-CN-YunxiNeural
```

### voices - 列出语音

查看可用的 TTS 语音列表。

```bash
python -m src.main voices
```

**可用中文语音**：

| 语音名称 | 描述 | 性别 |
|---------|------|------|
| zh-CN-XiaoxiaoNeural | 自然流畅 | 女 |
| zh-CN-YunyangNeural | 新闻播报风格 | 男 |
| zh-CN-YunxiNeural | 年轻活泼 | 男 |
| zh-CN-XiaoyiNeural | 温柔甜美 | 女 |

---

## GUI 版本

### 启动 GUI

```bash
# 方式一：直接运行
python -m src.gui

# 方式二：使用 Python 运行主窗口
python src/gui/main_window.py
```

### MOBI 提取功能

1. 点击 **"MOBI提取"** 标签页
2. 点击 **"浏览..."** 选择 MOBI 文件
3. 选择输出目录（默认为 `chapter/`）
4. 点击 **"开始提取"** 按钮
5. 等待进度条完成，查看日志输出

### 音频转换功能

1. 点击 **"音频转换"** 标签页
2. 选择章节目录（包含 `.md` 文件的目录）
3. 选择输出目录
4. 选择 TTS 引擎：
   - **Edge-TTS（推荐）**：高质量语音，需要网络
   - **ChatTTS（离线）**：完全离线，需要安装额外依赖
5. 选择语音类型
6. 点击 **"开始转换"** 按钮
7. 等待进度条完成，查看日志输出

### 界面说明

```
┌─────────────────────────────────────────────────┐
│  VoiceBook - 电子书转音频工具                     │
├─────────────────────────────────────────────────┤
│  [MOBI提取]  [音频转换]                          │
├─────────────────────────────────────────────────┤
│                                                 │
│  MOBI文件: [________________] [浏览...]          │
│  输出目录: [________________] [浏览...]          │
│                                                 │
│  进度: [████████████░░░░░░░░] 60%               │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ [INFO] 开始提取...                       │   │
│  │ [INFO] 正在解析MOBI文件...               │   │
│  │ [SUCCESS] 提取完成                       │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│        [开始提取]  [取消]                        │
│                                                 │
│  状态: 正在处理...                              │
└─────────────────────────────────────────────────┘
```

---

## 常见问题

### 1. Edge-TTS 出现 503 错误

**原因**：Edge-TTS 服务暂时不可用或网络问题。

**解决方案**：
- 稍后重试
- 检查网络连接
- 使用 ChatTTS 作为替代方案

### 2. ChatTTS 模型下载慢

**原因**：模型文件约 2GB，下载速度取决于网络。

**解决方案**：
- 使用代理或 VPN
- 手动下载模型到 `~/.cache/huggingface/` 目录
- 耐心等待首次下载完成

### 3. 音频质量问题

**Edge-TTS**：
- 语音质量优秀，接近真人水平
- 需要网络连接

**ChatTTS**：
- 语音自然，有情感
- 完全离线
- 需要较好的硬件支持

### 4. 内存不足

**ChatTTS 内存要求**：
- GPU 模式：至少 4GB 显存
- CPU 模式：至少 8GB 内存

**解决方案**：
- 使用 CPU 模式（速度较慢）
- 关闭其他占用内存的程序
- 使用 Edge-TTS 替代

### 5. 转换速度慢

**优化建议**：
- 使用 GPU 加速（ChatTTS）
- 减少同时处理的章节数量
- 使用 Edge-TTS（云端处理，速度快）

---

## 项目结构

```
voicebook/
├── books/              # 输入：电子书文件
├── chapter/            # 输出：章节文本
├── audios/             # 输出：音频文件
├── doc/                # 文档
├── logs/               # 日志文件
├── src/
│   ├── libs/           # 本地化的开源库
│   │   ├── mobi/       # MOBI 解析库
│   │   ├── edge_tts/   # Edge-TTS 库
│   │   └── chat_tts_converter.py
│   ├── mobi_handler/   # MOBI 提取模块
│   ├── tts/            # TTS 模块
│   ├── gui/            # GUI 界面
│   ├── utils/          # 工具模块
│   ├── config.py       # 配置文件
│   └── main.py         # 命令行入口
└── requirements.txt    # 依赖列表
```

---

## 技术支持

如遇问题，请查看：
1. 日志文件：`logs/` 目录下的日志文件
2. 使用示例：`src/voicebook_demo.py`
3. 调研文档：`doc/` 目录下的技术文档
