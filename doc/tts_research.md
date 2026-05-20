# 本地文字转语音(TTS)模型方案调研报告

## 概述

本文档针对本地文字转语音(TTS)模型方案进行调研，重点评估各方案在中文语音合成场景下的适用性，为项目技术选型提供参考。

---

## 一、主流TTS方案详细分析

### 1. Edge-TTS（微软Edge的TTS）

#### 简介
Edge-TTS是微软Edge浏览器在线TTS服务的Python封装库，通过调用微软Azure认知服务的公开API实现语音合成。

#### 优点
- **语音质量优秀**：使用微软Azure的高质量神经网络语音，中文语音自然流畅
- **中文支持完善**：提供多种中文语音选择（如zh-CN-YunyangNeural、zh-CN-XiaoxiaoNeural等）
- **安装简单**：`pip install edge-tts` 即可完成安装
- **无需GPU**：完全云端处理，本地无需GPU资源
- **免费使用**：无需付费，无需API密钥

#### 缺点
- **非完全离线**：需要网络连接，依赖微软服务器
- **隐私问题**：文本需要发送到云端处理
- **稳定性依赖网络**：网络不稳定时可能影响使用
- **不可本地化**：无法将源代码引入项目，依赖外部服务

#### 硬件要求
- CPU：任意
- GPU：无需
- 内存：极低（<100MB）
- 网络：必需

#### 推理速度
- 快速，实时因子约0.3-0.5x（受网络影响）

#### 使用示例
```python
import edge_tts
import asyncio

async def text_to_speech(text, output_file):
    communicate = edge_tts.Communicate(text, "zh-CN-YunyangNeural")
    await communicate.save(output_file)

asyncio.run(text_to_speech("你好，这是一个测试", "output.mp3"))
```

---

### 2. ChatTTS（开源中文TTS模型）

#### 简介
ChatTTS是2024年爆火的开源TTS模型，专为对话场景设计，使用超过10万小时的中英文数据训练。GitHub星标超过25k。

#### 优点
- **语音质量极佳**：韵律自然，能模拟真人语气、停顿、笑声等
- **中文支持优秀**：专门针对中文优化，中英混合效果好
- **完全离线**：可完全本地运行，无需网络
- **可本地化**：开源代码，可引入项目

#### 缺点
- **推理速度慢**：不适合实时场景，生成时间较长
- **稳定性问题**：同样参数多次生成结果可能不同
- **模型较大**：需要下载约2GB模型文件
- **资源占用高**：需要较好的GPU支持

#### 硬件要求
- CPU：可运行但较慢
- GPU：推荐NVIDIA显卡，显存≥4GB
- 内存：≥8GB
- 模型大小：约2GB

#### 推理速度
- 较慢，实时因子约2-5x（取决于硬件）

#### 使用示例
```python
import ChatTTS
import torch

chat = ChatTTS.Chat()
chat.load_models()

text = "你好，这是一个测试"
wavs = chat.infer(text)
```

---

### 3. Piper TTS（轻量级本地TTS）

#### 简介
Piper是一个快速、本地的神经网络TTS系统，专为边缘设备优化，使用ONNX格式模型。

#### 优点
- **轻量级**：模型小，资源占用低
- **完全离线**：无需网络
- **跨平台**：支持多种平台
- **推理速度快**：优化后速度较快
- **可本地化**：开源代码

#### 缺点
- **中文语音质量一般**：中文模型较少，质量不如其他方案
- **中文支持有限**：主要针对英文优化
- **语音自然度较低**：相比大模型，自然度有差距

#### 硬件要求
- CPU：可流畅运行
- GPU：无需
- 内存：约500MB-1GB
- 模型大小：约20-60MB

#### 推理速度
- 快速，实时因子约0.5-1x

---

### 4. Coqui TTS（功能强大的开源TTS）

#### 简介
Coqui TTS是一个功能强大的开源TTS库，支持多种模型架构（Tacotron2、VITS、Glow-TTS等），GitHub星标超过30k。

#### 优点
- **功能丰富**：支持多种模型架构和训练方式
- **可定制性强**：支持自定义训练和微调
- **完全离线**：无需网络
- **社区活跃**：文档完善，社区支持好
- **可本地化**：开源代码

#### 缺点
- **中文预训练模型少**：高质量中文模型有限
- **部署复杂**：配置和依赖较多
- **资源占用中等**：需要一定GPU资源
- **许可限制**：部分模型有商业使用限制

#### 硬件要求
- CPU：可运行但较慢
- GPU：推荐显存≥4GB
- 内存：≥4GB
- 模型大小：约500MB-2GB

#### 推理速度
- 中等，实时因子约1-2x

#### 使用示例
```python
from TTS.api import TTS

tts = TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC")
tts.tts_to_file(text="你好，这是一个测试", file_path="output.wav")
```

---

### 5. GPT-SoVITS（声音克隆TTS）

#### 简介
GPT-SoVITS是由RVC创始人开发的声音克隆TTS项目，支持少样本声音克隆，支持中英日三语。

#### 优点
- **声音克隆能力强**：仅需几秒音频即可克隆音色
- **语音质量高**：接近真人水平
- **多语言支持**：中文、英文、日文
- **完全离线**：可本地部署

#### 缺点
- **显存要求高**：至少6GB显存
- **部署复杂**：配置步骤多
- **推理速度慢**：不适合实时场景
- **主要用于克隆**：作为通用TTS使用较重

#### 硬件要求
- CPU：可运行但很慢
- GPU：显存≥6GB（推荐≥8GB）
- 内存：≥16GB
- 模型大小：约3-5GB

---

### 6. Fish Speech（低显存高性能TTS）

#### 简介
Fish Speech是2024年新推出的开源TTS模型，使用15万小时数据训练，以低显存占用和高语音质量著称。

#### 优点
- **显存要求低**：仅需4GB显存
- **语音质量高**：媲美GPT-SoVITS
- **多语言支持**：中英日三语支持优秀
- **完全离线**：可本地部署
- **快速部署**：有一键启动包

#### 缺点
- **项目较新**：社区生态不如老项目成熟
- **模型较大**：约2-3GB
- **推理速度中等**：比Piper慢

#### 硬件要求
- CPU：可运行
- GPU：显存≥4GB
- 内存：≥8GB
- 模型大小：约2-3GB

---

### 7. Sherpa-ONNX（轻量级跨平台TTS）

#### 简介
Sherpa-ONNX是基于ONNX格式的轻量级语音AI工具包，支持ASR、TTS、VAD等功能。

#### 优点
- **极轻量级**：可在嵌入式设备运行
- **跨平台**：支持多种平台和架构
- **完全离线**：无需网络
- **推理速度快**：优化后延迟低
- **可本地化**：开源代码

#### 缺点
- **中文语音质量一般**：不如大模型自然
- **功能相对简单**：定制性有限
- **中文模型较少**：选择有限

#### 硬件要求
- CPU：可流畅运行
- GPU：无需
- 内存：约200-500MB
- 模型大小：约30-100MB

---

### 8. pyttsx3（系统TTS封装）

#### 简介
pyttsx3是Python的离线TTS库，调用系统内置TTS引擎（Windows SAPI5、macOS NSSpeechSynthesizer、Linux espeak）。

#### 优点
- **完全离线**：无需网络
- **极轻量**：无额外依赖
- **跨平台**：支持主流操作系统
- **安装简单**：`pip install pyttsx3`
- **可本地化**：开源代码

#### 缺点
- **语音质量差**：机械音明显，不自然
- **中文支持弱**：依赖系统中文语音包
- **功能有限**：无法精细控制
- **不适合生产**：主要用于辅助功能

#### 硬件要求
- CPU：任意
- GPU：无需
- 内存：极低

---

## 二、方案对比表

| 方案 | 中文语音质量 | 模型大小 | GPU要求 | 内存要求 | 推理速度 | 完全离线 | 部署复杂度 | 可本地化 |
|------|-------------|---------|---------|---------|---------|---------|-----------|---------|
| Edge-TTS | ⭐⭐⭐⭐⭐ | 无需 | 无需 | <100MB | 快 | ❌ | 极简 | ❌ |
| ChatTTS | ⭐⭐⭐⭐⭐ | ~2GB | 推荐≥4GB | ≥8GB | 慢 | ✅ | 中等 | ✅ |
| Piper TTS | ⭐⭐⭐ | 20-60MB | 无需 | ~1GB | 快 | ✅ | 简单 | ✅ |
| Coqui TTS | ⭐⭐⭐⭐ | 0.5-2GB | 推荐≥4GB | ≥4GB | 中等 | ✅ | 复杂 | ✅ |
| GPT-SoVITS | ⭐⭐⭐⭐⭐ | 3-5GB | ≥6GB | ≥16GB | 慢 | ✅ | 复杂 | ✅ |
| Fish Speech | ⭐⭐⭐⭐⭐ | 2-3GB | ≥4GB | ≥8GB | 中等 | ✅ | 中等 | ✅ |
| Sherpa-ONNX | ⭐⭐⭐ | 30-100MB | 无需 | ~500MB | 快 | ✅ | 简单 | ✅ |
| pyttsx3 | ⭐⭐ | 无需 | 无需 | 极低 | 快 | ✅ | 极简 | ✅ |

---

## 三、推荐方案

### 主推荐：ChatTTS + Edge-TTS 混合方案

#### 选择理由

1. **ChatTTS作为主要离线引擎**
   - 中文语音质量最佳，接近真人水平
   - 完全离线运行，保护隐私
   - 开源可本地化，适合项目集成
   - 硬件要求适中（4GB显存即可）

2. **Edge-TTS作为备选/在线方案**
   - 安装极简，无需GPU
   - 语音质量优秀
   - 可作为离线不可用时的备选

#### 实施建议

```
优先级策略：
1. 首选 ChatTTS（离线高质量）
2. 备选 Edge-TTS（在线备选）
3. 降级 pyttsx3（极端情况）
```

### 备选推荐：Fish Speech

如果项目对显存有更严格要求（仅4GB），Fish Speech是更好的选择：
- 显存仅需4GB
- 语音质量同样优秀
- 部署相对简单

---

## 四、安装和使用指南

### ChatTTS 安装使用

```bash
# 安装
pip install ChatTTS

# 下载模型（首次使用自动下载）
```

```python
import ChatTTS
import torch
import torchaudio

# 初始化
chat = ChatTTS.Chat()
chat.load(compile=False)  # CPU模式使用compile=False

# 生成语音
text = "你好，欢迎使用语音合成系统。"
wavs = chat.infer([text])

# 保存音频
torchaudio.save("output.wav", torch.from_numpy(wavs[0]), 24000)
```

### Edge-TTS 安装使用

```bash
# 安装
pip install edge-tts
```

```python
import edge_tts
import asyncio

async def generate_speech(text, output_path, voice="zh-CN-YunyangNeural"):
    """
    使用Edge-TTS生成语音
    
    Args:
        text: 要转换的文本
        output_path: 输出文件路径
        voice: 语音名称
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# 使用示例
asyncio.run(generate_speech("你好，这是一个测试", "output.mp3"))

# 查看可用中文语音
async def list_voices():
    voices = await edge_tts.list_voices()
    for voice in voices:
        if voice["Locale"].startswith("zh-CN"):
            print(f"{voice['ShortName']}: {voice['FriendlyName']}")

asyncio.run(list_voices())
```

### 常用中文语音列表

| 语音名称 | 描述 |
|---------|------|
| zh-CN-YunyangNeural | 男声，新闻播报风格 |
| zh-CN-XiaoxiaoNeural | 女声，自然流畅 |
| zh-CN-YunxiNeural | 男声，年轻活泼 |
| zh-CN-XiaoyiNeural | 女声，温柔甜美 |
| zh-CN-YunjianNeural | 男声，沉稳大气 |

---

## 五、总结

根据调研结果，针对本项目（语音书籍生成）的需求：

1. **主要需求**：高质量中文语音、离线运行、可本地化
2. **推荐方案**：ChatTTS作为主引擎，Edge-TTS作为备选
3. **理由**：
   - ChatTTS中文语音质量最佳，完全离线
   - Edge-TTS作为备选，安装简单，质量优秀
   - 两者结合可覆盖各种使用场景

4. **注意事项**：
   - ChatTTS需要GPU支持以获得较好性能
   - 如无GPU，可考虑Fish Speech或使用Edge-TTS
   - 对于嵌入式或低资源场景，考虑Sherpa-ONNX

---

*调研日期：2026年3月*
*项目：VoiceBook 语音书籍生成系统*
