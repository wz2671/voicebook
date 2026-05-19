"""
环境变量配置中心

所有环境变量在此集中定义，包含默认值和注释说明。
启动时会自动从项目根目录的 .env.local 加载实际值（优先于默认值）。
.env.local 已加入 .gitignore，不会提交到版本管理。

使用方式:
    from env import env

    api_key = env.minimax_api_key
    voice_id = env.minimax_voice_id
"""

import os
from pathlib import Path
from typing import Optional


def _find_project_root() -> Path:
    """查找项目根目录（包含 src/ 的父目录）"""
    current = Path(__file__).resolve().parent.parent
    return current


_PROJECT_ROOT = _find_project_root()


def _load_env_local() -> dict:
    """
    从项目根目录的 .env.local 文件加载配置值。
    文件格式为 KEY=VALUE，每行一个，支持 # 注释和空行。
    """
    env_values = {}
    env_file = _PROJECT_ROOT / ".env.local"

    if not env_file.exists():
        return env_values

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            # 跳过格式不正确的行
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # 移除值两边的引号（支持 KEY="value" 和 KEY='value'）
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key:
                env_values[key] = value

    return env_values


# 加载 .env.local 中的值
_local_values = _load_env_local()


def _get(key: str, default: str = "") -> str:
    """
    获取配置值，优先级: 系统环境变量 > .env.local > 默认值
    """
    if key in os.environ:
        val = os.environ[key]
        # 即使来自系统环境变量，也去除引号
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        return val
    if key in _local_values:
        return _local_values[key]
    return default


class EnvConfig:
    """环境配置单例，集中管理所有配置项"""

    # ============================================================
    # Minimax TTS API 配置
    # ============================================================

    @property
    def minimax_api_key(self) -> str:
        """Minimax API 访问密钥，请前往 https://platform.minimax.io 获取"""
        return _get("MINIMAX_API_KEY", "")

    @property
    def minimax_model(self) -> str:
        """Minimax TTS 模型: speech-2.8-hd / speech-02-hd / speech-2.6-hd / speech-01 / speech-02"""
        return _get("MINIMAX_MODEL", "speech-2.8-hd")

    @property
    def minimax_voice_id(self) -> str:
        """Minimax 默认音色ID"""
        return _get("MINIMAX_VOICE_ID", "female-shaonv")

    @property
    def minimax_speed(self) -> float:
        """语速 (0.5 - 2.0)"""
        try:
            return float(_get("MINIMAX_SPEED", "1.0"))
        except ValueError:
            return 1.0

    @property
    def minimax_volume(self) -> float:
        """音量 (0.0 - 1.0)"""
        try:
            return float(_get("MINIMAX_VOLUME", "1.0"))
        except ValueError:
            return 1.0

    @property
    def minimax_pitch(self) -> int:
        """音调 (-12 ~ 12)"""
        try:
            return int(_get("MINIMAX_PITCH", "0"))
        except ValueError:
            return 0

    @property
    def minimax_sample_rate(self) -> int:
        """采样率 (8000, 16000, 22050, 24000, 32000, 44100, 48000)"""
        try:
            return int(_get("MINIMAX_SAMPLE_RATE", "32000"))
        except ValueError:
            return 32000

    @property
    def minimax_bitrate(self) -> int:
        """音频码率 (32000, 64000, 128000, 256000)"""
        try:
            return int(_get("MINIMAX_BITRATE", "128000"))
        except ValueError:
            return 128000

    @property
    def minimax_audio_format(self) -> str:
        """输出音频格式 (mp3, wav, pcm, flac)"""
        return _get("MINIMAX_AUDIO_FORMAT", "mp3")

    # ============================================================
    # 豆包（火山引擎）TTS API 配置
    # ============================================================

    @property
    def doubao_app_id(self) -> str:
        """火山引擎 APP ID，用于鉴权"""
        return _get("DOUBAO_APP_ID", "")

    @property
    def doubao_access_key(self) -> str:
        """火山引擎 Access Token，用于鉴权"""
        return _get("DOUBAO_ACCESS_KEY", "")

    @property
    def doubao_resource_id(self) -> str:
        """资源 ID: seed-tts-2.0 (模型2.0) / seed-tts-1.0 (模型1.0) / seed-icl-2.0 (声音复刻)"""
        return _get("DOUBAO_RESOURCE_ID", "seed-tts-2.0")

    @property
    def doubao_speaker(self) -> str:
        """默认发音人，见 https://www.volcengine.com/docs/6561/1257544"""
        return _get("DOUBAO_SPEAKER", "zh_female_vv_uranus_bigtts")

    @property
    def doubao_audio_format(self) -> str:
        """输出音频格式 (mp3, ogg_opus, pcm, wav)"""
        return _get("DOUBAO_AUDIO_FORMAT", "mp3")

    @property
    def doubao_sample_rate(self) -> int:
        """采样率 (8000, 16000, 22050, 24000, 32000, 44100, 48000)"""
        try:
            return int(_get("DOUBAO_SAMPLE_RATE", "24000"))
        except ValueError:
            return 24000

    @property
    def doubao_speech_rate(self) -> int:
        """语速 [-50, 100]，100=2.0倍速，-50=0.5倍速"""
        try:
            return int(_get("DOUBAO_SPEECH_RATE", "0"))
        except ValueError:
            return 0

    @property
    def doubao_emotion(self) -> str:
        """情感设置 (如 angry, happy)，仅部分音色支持"""
        return _get("DOUBAO_EMOTION", "")

    @property
    def doubao_emotion_scale(self) -> int:
        """情绪值 1~5，默认4"""
        try:
            return int(_get("DOUBAO_EMOTION_SCALE", "4"))
        except ValueError:
            return 4

    @property
    def doubao_volume_ratio(self) -> float:
        """音量比率 (0.5 ~ 2.0)，默认 1.0。固定值避免音量波动"""
        try:
            return float(_get("DOUBAO_VOLUME_RATIO", "1.0"))
        except ValueError:
            return 1.0

    @property
    def doubao_loudness_rate(self) -> int:
        """响度归一化: 0=标准(推荐), 1=增强, 2=关闭。设为0强制响度对齐，抑制句间跳变"""
        try:
            return int(_get("DOUBAO_LOUDNESS_RATE", "0"))
        except ValueError:
            return 0

    # ============================================================
    # Edge TTS 配置（微软免费 TTS）
    # ============================================================

    @property
    def edge_tts_default_voice(self) -> str:
        """Edge TTS 默认语音"""
        return _get("EDGE_TTS_VOICE", "zh-CN-XiaoxiaoNeural")

    # ============================================================
    # ChatTTS 配置（本地 TTS 模型）
    # ============================================================

    @property
    def chat_tts_use_gpu(self) -> bool:
        """ChatTTS 是否使用 GPU"""
        return _get("CHAT_TTS_USE_GPU", "true").lower() in ("1", "true", "yes")

    # ============================================================
    # 应用通用配置
    # ============================================================

    @property
    def audio_format(self) -> str:
        """输出音频格式（全局默认）"""
        return _get("AUDIO_FORMAT", "mp3")

    @property
    def log_level(self) -> str:
        """日志级别: DEBUG, INFO, WARNING, ERROR"""
        return _get("LOG_LEVEL", "INFO")

    # ============================================================
    # ChatTTS / 深度学习相关环境变量（运行时设置）
    # ============================================================

    @property
    def vllm_use_modelscope(self) -> str:
        """ChatTTS: 使用 ModelScope 下载模型"""
        return _get("VLLM_USE_MODELSCOPE", "False")

    @property
    def ray_usage_stats_enabled(self) -> str:
        """ChatTTS: Ray 使用统计"""
        return _get("RAY_USAGE_STATS_ENABLED", "0")

    @property
    def torch_nccl_avoid_record_streams(self) -> str:
        """ChatTTS: NCCL 流优化"""
        return _get("TORCH_NCCL_AVOID_RECORD_STREAMS", "1")


# 全局单例
env = EnvConfig()


# 自动将 ChatTTS 相关环境变量注入到 os.environ
# 这样现有的 chat_tts 库无需修改即可读取配置
def _inject_env_vars():
    """将 env.py 管理的配置注入到 os.environ（仅当 os.environ 未设置时）"""
    _vars = {
        "VLLM_USE_MODELSCOPE": env.vllm_use_modelscope,
        "RAY_USAGE_STATS_ENABLED": env.ray_usage_stats_enabled,
        "TORCH_NCCL_AVOID_RECORD_STREAMS": env.torch_nccl_avoid_record_streams,
    }
    for key, value in _vars.items():
        if key not in os.environ:
            os.environ[key] = value


_inject_env_vars()


if __name__ == "__main__":
    print("=" * 60)
    print("VoiceBook 环境配置")
    print("=" * 60)

    print(f"\n{'配置项':<35} {'值':<25} {'来源'}")
    print("-" * 80)

    config_items = [
        # Doubao
        ("DOUBAO_APP_ID", env.doubao_app_id[:8] + "***" if env.doubao_app_id else "(未设置)", "env/env.local"),
        ("DOUBAO_ACCESS_KEY", env.doubao_access_key[:8] + "***" if env.doubao_access_key else "(未设置)", "env/env.local"),
        ("DOUBAO_RESOURCE_ID", env.doubao_resource_id, "env.local"),
        ("DOUBAO_SPEAKER", env.doubao_speaker, "env.local"),
        ("DOUBAO_AUDIO_FORMAT", env.doubao_audio_format, "env.local"),
        ("DOUBAO_SAMPLE_RATE", str(env.doubao_sample_rate), "env.local"),
        ("DOUBAO_SPEECH_RATE", str(env.doubao_speech_rate), "env.local"),
        ("DOUBAO_EMOTION", env.doubao_emotion or "(未设置)", "env.local"),
        ("DOUBAO_EMOTION_SCALE", str(env.doubao_emotion_scale), "env.local"),
        # Minimax
        ("MINIMAX_API_KEY", env.minimax_api_key[:8] + "***" if env.minimax_api_key else "(未设置)", "env/env.local"),
        ("MINIMAX_MODEL", env.minimax_model, "env.local"),
        ("MINIMAX_VOICE_ID", env.minimax_voice_id, "env.local"),
        ("MINIMAX_SPEED", str(env.minimax_speed), "env.local"),
        ("MINIMAX_VOLUME", str(env.minimax_volume), "env.local"),
        ("MINIMAX_PITCH", str(env.minimax_pitch), "env.local"),
        ("MINIMAX_SAMPLE_RATE", str(env.minimax_sample_rate), "env.local"),
        ("MINIMAX_BITRATE", str(env.minimax_bitrate), "env.local"),
        ("MINIMAX_AUDIO_FORMAT", env.minimax_audio_format, "env.local"),
        # Edge TTS
        ("EDGE_TTS_VOICE", env.edge_tts_default_voice, "env.local"),
        # ChatTTS
        ("CHAT_TTS_USE_GPU", str(env.chat_tts_use_gpu), "env.local"),
        # App
        ("AUDIO_FORMAT", env.audio_format, "env.local"),
        ("LOG_LEVEL", env.log_level, "env.local"),
        # Internal
        ("VLLM_USE_MODELSCOPE", env.vllm_use_modelscope, "env.local"),
        ("RAY_USAGE_STATS_ENABLED", env.ray_usage_stats_enabled, "env.local"),
        ("TORCH_NCCL_AVOID_RECORD_STREAMS", env.torch_nccl_avoid_record_streams, "env.local"),
    ]

    for name, value, source in config_items:
        print(f"  {name:<33} {value:<25} ({source})")

    print("\n" + "=" * 60)
    print(f"项目根目录: {_PROJECT_ROOT}")
    print(f".env.local 路径: {_PROJECT_ROOT / '.env.local'}")
    print(f".env.local 存在: {(_PROJECT_ROOT / '.env.local').exists()}")
