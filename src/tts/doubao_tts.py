"""
豆包（火山引擎）TTS 语音合成引擎

使用火山引擎异步长文本 TTS API v3 将文字转换为语音。
采用 Submit → Query 轮询 → 下载 的异步模式。
单次最大 10 万字符，合成音频在服务端保存 7 天。

配置通过 src/env.py 管理，实际值在项目根目录的 .env.local 中设置。

API 文档: https://www.volcengine.com/docs/6561/1257544
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import List, Optional

import requests

from env import env as _env_config

logger = logging.getLogger(__name__)


class DoubaoTTS:
    """豆包（火山引擎）TTS 引擎，通过异步 Submit/Query API 生成语音"""

    # 火山引擎 API 端点
    SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/tts/submit"
    QUERY_URL = "https://openspeech.bytedance.com/api/v3/tts/query"

    # 轮询配置
    POLL_INTERVAL = 2
    POLL_TIMEOUT = 600

    # seed-tts-2.0 中文音色（uranus/jupiter_bigtts 系列）
    CHINESE_VOICES_2_0 = [
        {"voice_id": "zh_female_vv_uranus_bigtts", "name": "女声-vv(推荐)", "gender": "Female",
         "description": "活泼灵动女声，有很强分享欲", "resource_id": "seed-tts-2.0"},
        {"voice_id": "zh_female_xiaohe_jupiter_bigtts", "name": "女声-小荷", "gender": "Female",
         "description": "甜美活泼女声，明显台湾口音", "resource_id": "seed-tts-2.0"},
        {"voice_id": "zh_male_yunzhou_jupiter_bigtts", "name": "男声-云舟", "gender": "Male",
         "description": "清爽沉稳男声", "resource_id": "seed-tts-2.0"},
        {"voice_id": "zh_male_xiaotian_jupiter_bigtts", "name": "男声-小天", "gender": "Male",
         "description": "清爽磁性男声", "resource_id": "seed-tts-2.0"},
        {"voice_id": "zh_female_xueayi_saturn_bigtts", "name": "女声-儿童绘本", "gender": "Female",
         "description": "儿童绘本阅读，温暖亲切", "resource_id": "seed-tts-2.0"},
    ]

    # seed-tts-2.0 英文音色（uranus_bigtts 系列）
    ENGLISH_VOICES_2_0 = [
        {"voice_id": "en_male_tim_uranus_bigtts", "name": "Tim", "gender": "Male",
         "description": "美式英语男声", "resource_id": "seed-tts-2.0"},
        {"voice_id": "en_female_dacey_uranus_bigtts", "name": "Dacey", "gender": "Female",
         "description": "美式英语女声", "resource_id": "seed-tts-2.0"},
        {"voice_id": "en_female_stokie_uranus_bigtts", "name": "Stokie", "gender": "Female",
         "description": "美式英语女声", "resource_id": "seed-tts-2.0"},
    ]

    # seed-tts-1.0 音色（mars/moon/wvae_bigtts / ICL 系列）
    CHINESE_VOICES_1_0 = [
        {"voice_id": "zh_female_vv_mars_bigtts", "name": "女声-vivi 1.0", "gender": "Female",
         "description": "活泼可爱女声，支持多情感", "resource_id": "seed-tts-1.0"},
        {"voice_id": "zh_male_ahu_conversation_wvae_bigtts", "name": "男声-阿虎", "gender": "Male",
         "description": "通用男声", "resource_id": "seed-tts-1.0"},
        {"voice_id": "ICL_zh_female_chengshu_v1_tob", "name": "女声-成熟温柔", "gender": "Female",
         "description": "成熟温柔女声(复刻)", "resource_id": "seed-icl-1.0"},
        {"voice_id": "ICL_zh_female_tianmei_v1_tob", "name": "女声-甜美活泼", "gender": "Female",
         "description": "甜美活泼女声(复刻)", "resource_id": "seed-icl-1.0"},
    ]

    # 合并所有预设音色（用于 voices 命令展示）
    CHINESE_VOICES = CHINESE_VOICES_2_0 + CHINESE_VOICES_1_0

    # speaker 后缀/前缀 → resource_id 映射
    _SPEAKER_RESOURCE_MAP_SUFFIX = {
        "_jupiter_bigtts": "seed-tts-2.0",
        "_uranus_bigtts": "seed-tts-2.0",
        "_saturn_bigtts": "seed-tts-2.0",
        "_moon_bigtts": "seed-tts-1.0",
        "_mars_bigtts": "seed-tts-1.0",
        "_wvae_bigtts": "seed-tts-1.0",
    }
    _SPEAKER_RESOURCE_MAP_PREFIX = {
        "ICL_": "seed-icl-1.0",
        "S_": "seed-icl-2.0",
    }

    def __init__(
        self,
        app_id: Optional[str] = None,
        access_key: Optional[str] = None,
        resource_id: Optional[str] = None,
        speaker: Optional[str] = None,
        audio_format: Optional[str] = None,
        sample_rate: Optional[int] = None,
        speech_rate: Optional[int] = None,
        emotion: Optional[str] = None,
        emotion_scale: Optional[int] = None,
    ):
        self.app_id = app_id or _env_config.doubao_app_id
        if not self.app_id:
            raise ValueError(
                "豆包 APP ID 未设置。请通过以下任一方式提供：\n"
                "  1. 在 .env.local 中设置 DOUBAO_APP_ID=your_id\n"
                "  2. 设置环境变量: export DOUBAO_APP_ID=your_id\n"
                "  3. 代码传入: DoubaoTTS(app_id='your_id')"
            )

        self.access_key = access_key or _env_config.doubao_access_key
        if not self.access_key:
            raise ValueError("豆包 Access Key 未设置，请在 .env.local 中设置 DOUBAO_ACCESS_KEY")

        self.speaker = speaker or _env_config.doubao_speaker
        # 根据 speaker 后缀/前缀自动推断 resource_id，避免 55000000 不匹配错误
        # 后缀: _jupiter_bigtts/_uranus_bigtts/_saturn_bigtts → seed-tts-2.0
        #       _moon_bigtts/_mars_bigtts/_wvae_bigtts → seed-tts-1.0
        # 前缀: ICL_ → seed-icl-1.0, S_ → seed-icl-2.0
        inferred_resource_id = None
        for suffix, rid in self._SPEAKER_RESOURCE_MAP_SUFFIX.items():
            if self.speaker.endswith(suffix):
                inferred_resource_id = rid
                break
        if inferred_resource_id is None:
            for prefix, rid in self._SPEAKER_RESOURCE_MAP_PREFIX.items():
                if self.speaker.startswith(prefix):
                    inferred_resource_id = rid
                    break
        if inferred_resource_id and not resource_id:
            self.resource_id = inferred_resource_id
        else:
            self.resource_id = resource_id or _env_config.doubao_resource_id
        self.audio_format = audio_format or _env_config.doubao_audio_format
        self.sample_rate = sample_rate if sample_rate is not None else _env_config.doubao_sample_rate
        self.speech_rate = speech_rate if speech_rate is not None else _env_config.doubao_speech_rate
        self.emotion = emotion if emotion is not None else _env_config.doubao_emotion
        self.emotion_scale = emotion_scale if emotion_scale is not None else _env_config.doubao_emotion_scale

    def _build_headers(self) -> dict:
        return {
            "X-Api-App-Id": self.app_id,
            "X-Api-Access-Key": self.access_key,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }

    def _build_submit_body(self, text: str) -> dict:
        body = {
            "user": {"uid": "voicebook"},
            "unique_id": str(uuid.uuid4()),
            "req_params": {
                "text": text,
                "speaker": self.speaker,
                "audio_params": {
                    "format": self.audio_format,
                    "sample_rate": self.sample_rate,
                    "speech_rate": self.speech_rate,
                },
            },
        }

        if self.emotion:
            body["req_params"]["audio_params"]["emotion"] = self.emotion
            body["req_params"]["audio_params"]["emotion_scale"] = self.emotion_scale

        return body

    def _submit_task(self, text: str) -> Optional[str]:
        """提交异步合成任务，返回 task_id"""
        headers = self._build_headers()
        body = self._build_submit_body(text)

        logger.info(f"提交豆包异步任务 (speaker={self.speaker}, format={self.audio_format}, "
                      f"sample_rate={self.sample_rate}, text_len={len(text)})")

        try:
            resp = requests.post(self.SUBMIT_URL, headers=headers, json=body, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"提交请求失败: {e}")
            return None

        if resp.status_code != 200:
            logger.error(f"提交失败 (HTTP {resp.status_code}): {resp.text[:500]}")
            return None

        result = resp.json()
        code = result.get("code")
        if code != 20000000:
            logger.error(f"提交错误: code={code}, message={result.get('message', '')}")
            return None

        task_id = result.get("data", {}).get("task_id")
        if not task_id:
            logger.error("未获取到 task_id")
            return None

        logger.info(f"任务已提交，task_id: {task_id}")
        return task_id

    def _poll_task(self, task_id: str) -> Optional[str]:
        """轮询直到任务完成，返回 audio_url"""
        headers = self._build_headers()
        body = {"task_id": task_id}

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self.POLL_TIMEOUT:
                logger.error(f"任务轮询超时 ({self.POLL_TIMEOUT}s)")
                return None

            time.sleep(self.POLL_INTERVAL)

            try:
                resp = requests.post(self.QUERY_URL, headers=headers, json=body, timeout=30)
            except requests.exceptions.RequestException as e:
                logger.warning(f"查询请求异常: {e}，继续等待...")
                continue

            if resp.status_code != 200:
                logger.warning(f"查询返回 HTTP {resp.status_code}，继续等待...")
                continue

            result = resp.json()
            code = result.get("code")
            if code != 20000000:
                logger.error(f"查询错误: code={code}, message={result.get('message', '')}")
                return None

            task_status = result.get("data", {}).get("task_status")
            if task_status == 2:  # Success
                audio_url = result.get("data", {}).get("audio_url")
                if audio_url:
                    logger.info(f"任务完成，耗时 {elapsed:.1f}s")
                    return audio_url
                logger.error("任务成功但未返回 audio_url")
                return None
            elif task_status == 3:  # Failure
                logger.error("任务处理失败")
                return None
            else:
                logger.debug(f"任务状态: {task_status}, 已等待 {elapsed:.0f}s")

    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """从 URL 下载音频文件"""
        logger.info("下载音频文件...")
        try:
            resp = requests.get(audio_url, timeout=60)
        except requests.exceptions.RequestException as e:
            logger.error(f"下载失败: {e}")
            return None

        if resp.status_code != 200:
            logger.error(f"下载失败 (HTTP {resp.status_code}): {resp.text[:500]}")
            return None

        logger.info(f"音频下载成功 ({len(resp.content) / 1024:.1f} KB)")
        return resp.content

    def text_to_speech(self, text: str, output_path: str) -> bool:
        """
        将文本转换为语音并保存到文件。

        Args:
            text: 要转换的文本（最大 10 万字符）
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
            audio_url = self._poll_task(task_id)
            if not audio_url:
                return False

            # 步骤 3: 下载音频文件
            audio_bytes = self._download_audio(audio_url)
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
        """获取可用的预设音色列表"""
        return cls.CHINESE_VOICES.copy()

    @classmethod
    def is_available(cls) -> bool:
        """检查依赖是否可用"""
        try:
            import requests  # noqa: F401
            return True
        except ImportError:
            return False


# === 注册到引擎中心 ===
from .registry import TTSEngineRegistry, EngineMeta

TTSEngineRegistry.register(EngineMeta(
    engine_id="doubao",
    display_name="豆包TTS (火山引擎)",
    engine_cls=DoubaoTTS,
    voices=DoubaoTTS.CHINESE_VOICES,
    default_voice=_env_config.doubao_speaker,
    is_available=DoubaoTTS.is_available,
))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("豆包 TTS 测试")
    print("=" * 60)

    if not DoubaoTTS.is_available():
        print("请先安装依赖: pip install requests")
        import sys
        sys.exit(1)

    if not _env_config.doubao_app_id or not _env_config.doubao_access_key:
        print("\n未配置豆包 API 凭据，请在 .env.local 中设置:")
        print("  DOUBAO_APP_ID=your_app_id")
        print("  DOUBAO_ACCESS_KEY=your_access_key")
        import sys
        sys.exit(1)

    print("\n可用音色:")
    for v in DoubaoTTS.get_available_voices():
        print(f"  {v['voice_id']} ({v['name']}) - {v['description']}")

    print("\n" + "-" * 60)

    try:
        tts = DoubaoTTS()
    except ValueError as e:
        print(f"初始化失败: {e}")
        import sys
        sys.exit(1)

    test_text = "你好，欢迎使用豆包语音合成服务。这是一个测试示例。"
    output_file = Path(__file__).parent / "test_doubao_output.mp3"

    print(f"\n测试文本: {test_text}")
    print(f"输出路径: {output_file}")
    print(f"发音人: {tts.speaker}")
    print(f"音频格式: {tts.audio_format}")
    print()

    success = tts.text_to_speech(test_text, str(output_file))

    if success:
        print(f"\n测试成功! 音频文件: {output_file}")
        print(f"文件大小: {output_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n测试失败!")
        import sys
        sys.exit(1)
