"""
Minimax TTS 语音合成引擎

使用 Minimax 异步长文本 API 将文字转换为语音。
支持 speech-2.8-hd 等最新高品质模型，单次最高 100 万字符。

配置通过 src/env.py 管理，实际值在项目根目录的 .env.local 中设置。

依赖安装:
    pip install requests

API 文档参考: https://platform.minimax.io/docs
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List
import logging

import requests

from env import env as _env_config

logger = logging.getLogger(__name__)


class MinimaxTTS:
    """Minimax TTS 引擎，通过异步长文本 API 生成语音"""

    # Minimax 异步长文本 API v2
    TTS_SUBMIT_ENDPOINT = "https://api.minimax.chat/v1/t2a_async_v2"
    TTS_QUERY_ENDPOINT = "https://api.minimax.chat/v1/query/t2a_async_query_v2"
    TTS_FILE_ENDPOINT = "https://api.minimax.chat/v1/files/retrieve_content"

    # 可用模型（推荐 speech-2.8-hd）
    MODELS = [
        "speech-2.8-hd",   # 新一代高品质，情绪渲染强，融合语气词
        "speech-02-hd",    # 经典高品质，韵律出色
        "speech-2.6-hd",   # 均衡型
        "speech-01",       # 基础模型
        "speech-02",       # 基础模型
    ]

    # 异步轮询配置
    POLL_INTERVAL = 2       # 轮询间隔（秒）
    POLL_TIMEOUT = 600      # 轮询超时（秒）

    # 预设中文音色
    CHINESE_VOICES = [
        {"voice_id": "male-qn-qingse",  "name": "青涩青年音色",    "gender": "Male",   "description": "年轻男声，清澈自然"},
        {"voice_id": "male-qn-jingying", "name": "精英青年音色",    "gender": "Male",   "description": "成熟男声，专业稳重"},
        {"voice_id": "male-qn-badao",    "name": "霸道青年音色",    "gender": "Male",   "description": "强势男声，有力沉稳"},
        {"voice_id": "male-qn-daxuesheng", "name": "大学生青年音色", "gender": "Male",  "description": "青春男声，学生气息"},
        {"voice_id": "female-shaonv",    "name": "少女音色",        "gender": "Female", "description": "年轻女声，甜美活泼"},
        {"voice_id": "female-yujie",     "name": "御姐音色",        "gender": "Female", "description": "成熟女声，优雅知性"},
        {"voice_id": "female-chengshu",  "name": "成熟女性音色",    "gender": "Female", "description": "稳重女声，温柔大方"},
        {"voice_id": "female-tianmei",   "name": "甜美女性音色",    "gender": "Female", "description": "甜美女声，亲切可爱"},
        {"voice_id": "presenter_male",   "name": "男性主持人",      "gender": "Male",   "description": "男主持风格，字正腔圆"},
        {"voice_id": "presenter_female", "name": "女性主持人",      "gender": "Female", "description": "女主持风格，清晰自然"},
        {"voice_id": "male-qn-qingse-jingpin",  "name": "青涩青年(精品)",  "gender": "Male",   "description": "精品男声，高保真"},
        {"voice_id": "female-shaonv-jingpin",   "name": "少女(精品)",      "gender": "Female", "description": "精品女声，高保真"},
        {"voice_id": "female-yujie-jingpin",    "name": "御姐(精品)",      "gender": "Female", "description": "精品女声，高保真"},
        {"voice_id": "female-chengshu-jingpin", "name": "成熟女性(精品)",  "gender": "Female", "description": "精品女声，高保真"},
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        voice_id: Optional[str] = None,
        speed: Optional[float] = None,
        volume: Optional[float] = None,
        pitch: Optional[int] = None,
        sample_rate: Optional[int] = None,
        bitrate: Optional[int] = None,
        audio_format: Optional[str] = None,
    ):
        # 参数优先，未传则从 env.py 配置中心读取
        self.api_key = api_key or _env_config.minimax_api_key
        if not self.api_key:
            raise ValueError(
                "Minimax API Key 未设置。请通过以下任一方式提供：\n"
                "  1. 在项目根目录 .env.local 中设置 MINIMAX_API_KEY=your_key\n"
                "  2. 设置环境变量: export MINIMAX_API_KEY=your_key\n"
                "  3. 代码传入: MinimaxTTS(api_key='your_key')"
            )

        self.model = model or _env_config.minimax_model
        if self.model not in self.MODELS:
            raise ValueError(f"无效模型: {self.model}，可选: {self.MODELS}")

        self.voice_id = voice_id or _env_config.minimax_voice_id
        self.speed = speed if speed is not None else _env_config.minimax_speed
        self.volume = volume if volume is not None else _env_config.minimax_volume
        self.pitch = pitch if pitch is not None else _env_config.minimax_pitch
        self.sample_rate = sample_rate if sample_rate is not None else _env_config.minimax_sample_rate
        self.bitrate = bitrate if bitrate is not None else _env_config.minimax_bitrate
        self.audio_format = audio_format or _env_config.minimax_audio_format

    def _build_request_body(self, text: str) -> dict:
        """构建异步 API v2 请求体"""
        return {
            "model": self.model,
            "text": text,
            "voice_setting": {
                "voice_id": self.voice_id,
                "speed": self.speed,
                "vol": self.volume,
                "pitch": self.pitch,
            },
            "audio_setting": {
                "audio_sample_rate": self.sample_rate,
                "bitrate": self.bitrate,
                "format": self.audio_format,
                "channel": 1,
            },
        }

    def _submit_task(self, text: str) -> Optional[int]:
        """提交异步语音合成任务，返回 task_id (int)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = self._build_request_body(text)

        logger.info(f"提交异步任务 (model={self.model}, voice={self.voice_id}, text_len={len(text)})")

        resp = requests.post(
            self.TTS_SUBMIT_ENDPOINT,
            headers=headers,
            json=body,
            timeout=30,
        )

        if resp.status_code != 200:
            logger.error(f"提交失败 (HTTP {resp.status_code}): {resp.text}")
            return None

        result = resp.json()
        base_resp = result.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            logger.error(f"提交错误: {base_resp.get('status_msg', 'unknown error')}")
            return None

        task_id = result.get("task_id")
        if not task_id:
            logger.error("未获取到 task_id")
            return None

        logger.info(f"任务已提交，task_id: {task_id}")
        return task_id

    def _poll_task(self, task_id: int) -> Optional[int]:
        """轮询异步任务直到完成，返回 file_id"""
        url = f"{self.TTS_QUERY_ENDPOINT}?task_id={task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self.POLL_TIMEOUT:
                logger.error(f"任务轮询超时 ({self.POLL_TIMEOUT}s)")
                return None

            time.sleep(self.POLL_INTERVAL)

            resp = requests.get(url, headers=headers, timeout=30)

            if resp.status_code != 200:
                logger.warning(f"查询返回 HTTP {resp.status_code}, 继续等待...")
                continue

            result = resp.json()

            base_resp = result.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                logger.error(f"查询错误: {base_resp.get('status_msg', 'unknown error')}")
                return None

            status = result.get("status", "")

            if status == "Success":
                file_id = result.get("file_id")
                if file_id:
                    elapsed_str = f"{elapsed:.1f}s"
                    logger.info(f"任务完成，耗时 {elapsed_str}，file_id: {file_id}")
                    return file_id
                logger.error("任务成功但未返回 file_id")
                return None

            elif status == "Failed":
                logger.error("任务处理失败")
                return None

            else:
                logger.debug(f"任务状态: {status}, 已等待 {elapsed:.0f}s")

    def _download_audio(self, file_id: int) -> Optional[bytes]:
        """通过 file_id 下载音频文件，返回原始字节"""
        url = f"{self.TTS_FILE_ENDPOINT}?file_id={file_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        logger.info(f"下载音频文件 file_id={file_id}...")
        resp = requests.get(url, headers=headers, timeout=60)

        if resp.status_code != 200:
            logger.error(f"下载失败 (HTTP {resp.status_code}): {resp.text[:500]}")
            return None

        logger.info(f"音频下载成功 ({len(resp.content) / 1024:.1f} KB)")
        return resp.content

    def text_to_speech(self, text: str, output_path: str) -> bool:
        """
        将文本转换为语音并保存到文件（使用异步长文本 API v2）。

        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径

        Returns:
            bool: 转换是否成功
        """
        if not text or not text.strip():
            logger.warning("文本为空，跳过转换")
            return False

        try:
            # 步骤 1: 提交异步任务
            task_id = self._submit_task(text)
            if not task_id:
                return False

            # 步骤 2: 轮询等待完成
            logger.info(f"等待语音合成完成 (最多 {self.POLL_TIMEOUT}s)...")
            file_id = self._poll_task(task_id)
            if not file_id:
                return False

            # 步骤 3: 下载音频文件
            audio_bytes = self._download_audio(file_id)
            if not audio_bytes:
                return False

            # 步骤 4: 写入本地文件
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            file_size = len(audio_bytes)
            logger.info(f"音频保存成功: {output_path} ({file_size / 1024:.1f} KB)")
            return True

        except requests.exceptions.Timeout:
            logger.error("API 请求超时")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("API 连接失败，请检查网络")
            return False
        except Exception as e:
            logger.error(f"转换失败: {e}")
            return False

    @classmethod
    def get_available_voices(cls) -> List[dict]:
        """获取可用的预设中文音色列表"""
        return cls.CHINESE_VOICES.copy()

    @classmethod
    def is_available(cls) -> bool:
        """检查 Minimax SDK/依赖 是否可用"""
        try:
            import requests
            return True
        except ImportError:
            return False


def create_minimax_tts(
    api_key: Optional[str] = None,
    voice_id: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs,
) -> Optional[MinimaxTTS]:
    """
    创建 MinimaxTTS 实例的工厂函数。
    所有参数可选，未传则从 env.py 配置中心读取。

    Returns:
        MinimaxTTS 实例，如果不可用或配置错误则返回 None
    """
    if not MinimaxTTS.is_available():
        logger.warning("requests 库未安装，请执行: pip install requests")
        return None

    try:
        return MinimaxTTS(
            api_key=api_key,
            voice_id=voice_id,
            model=model,
            **kwargs,
        )
    except ValueError as e:
        logger.error(str(e))
        return None


# === 注册到引擎中心 ===
from .registry import TTSEngineRegistry, EngineMeta

TTSEngineRegistry.register(EngineMeta(
    engine_id="minimax",
    display_name="Minimax TTS",
    engine_cls=MinimaxTTS,
    voices=MinimaxTTS.CHINESE_VOICES,
    default_voice=_env_config.minimax_voice_id,
    is_available=MinimaxTTS.is_available,
))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("Minimax TTS 测试")
    print("=" * 60)

    # 检查依赖
    if not MinimaxTTS.is_available():
        print("请先安装依赖: pip install requests")
        sys.exit(1)

    # 检查 API Key（从 env.py 配置中心读取）
    if not _env_config.minimax_api_key:
        print("\n未配置 MINIMAX_API_KEY，请在 .env.local 中设置:")
        print("  MINIMAX_API_KEY=your_api_key_here")
        print("\n或设置环境变量:")
        print("  export MINIMAX_API_KEY=your_api_key_here")
        sys.exit(1)

    # 列出可用音色
    print("\n可用中文音色:")
    for v in MinimaxTTS.get_available_voices():
        print(f"  {v['voice_id']} ({v['name']}) - {v['description']}")

    print("\n" + "-" * 60)

    try:
        tts = MinimaxTTS()
    except ValueError as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

    test_text = "你好，欢迎使用Minimax语音合成服务。这是一个测试示例。"
    output_file = Path(__file__).parent / "test_minimax_output.mp3"

    print(f"\n测试文本: {test_text}")
    print(f"输出路径: {output_file}")
    print(f"使用模型: {tts.model}")
    print(f"使用音色: {tts.voice_id}")
    print()

    success = tts.text_to_speech(test_text, str(output_file))

    if success:
        print(f"\n测试成功! 音频文件: {output_file}")
        print(f"文件大小: {output_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n测试失败!")
        sys.exit(1)

