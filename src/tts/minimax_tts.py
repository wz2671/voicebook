"""
Minimax TTS 语音合成引擎

使用 Minimax API 将文字转换为语音。
配置通过 src/env.py 管理，实际值在项目根目录的 .env.local 中设置。

依赖安装:
    pip install requests

API 文档参考: https://platform.minimax.io/docs
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import logging

import requests

from env import env as _env_config

logger = logging.getLogger(__name__)


class MinimaxTTS:
    """Minimax TTS 引擎，通过 HTTP API 生成语音"""

    # Minimax API 端点
    TTS_ENDPOINT = "https://api.minimax.chat/v1/t2a_v2"

    # 可用模型
    MODELS = ["speech-01", "speech-02"]

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
        return {
            "model": self.model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": self.voice_id,
                "speed": self.speed,
                "vol": self.volume,
                "pitch": self.pitch,
            },
            "audio_setting": {
                "sample_rate": self.sample_rate,
                "bitrate": self.bitrate,
                "format": self.audio_format,
            },
        }

    def _decode_audio(self, hex_audio: str) -> bytes:
        """将 Minimax 返回的十六进制音频数据解码为字节"""
        return bytes.fromhex(hex_audio)

    def text_to_speech(self, text: str, output_path: str) -> bool:
        """
        将文本转换为语音并保存到文件。

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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            body = self._build_request_body(text)

            logger.info(f"正在调用 Minimax API (model={self.model}, voice={self.voice_id})...")
            logger.debug(f"文本长度: {len(text)} 字符")

            resp = requests.post(
                self.TTS_ENDPOINT,
                headers=headers,
                json=body,
                timeout=60,
            )

            if resp.status_code != 200:
                logger.error(f"API 请求失败 (HTTP {resp.status_code}): {resp.text}")
                return False

            result = resp.json()

            # 检查响应状态
            base_resp = result.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                logger.error(f"API 返回错误: {base_resp.get('status_msg', 'unknown error')}")
                return False

            # 获取音频数据
            audio_data = result.get("data", {}).get("audio")
            if not audio_data:
                # speech-02 的响应格式稍有不同
                audio_data = result.get("audio")

            if not audio_data:
                logger.error("API 响应中未找到音频数据")
                return False

            # 解码并写入文件
            audio_bytes = self._decode_audio(audio_data)

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
        except ValueError as e:
            logger.error(f"十六进制解码失败: {e}")
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
