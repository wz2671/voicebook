"""
Minimax TTS 引擎单元测试

测试 MinimaxTTS 初始化、配置加载、API 请求构建、音频解码等功能。
API 调用测试仅在设置了 MINIMAX_API_KEY 时运行。
"""

import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_module_import():
    """测试模块导入和依赖检查"""
    print("=" * 60)
    print("测试 1: 模块导入和可用性检查")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    assert MinimaxTTS.is_available(), "requests should be installed"
    print("[PASS] MinimaxTTS 模块导入成功")
    print(f"[PASS] requests 依赖可用")


def test_voice_list():
    """测试音色列表"""
    print("\n" + "=" * 60)
    print("测试 2: 音色列表")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    voices = MinimaxTTS.get_available_voices()
    assert len(voices) == 14, f"expected 14 voices, got {len(voices)}"

    # 检查必要字段
    for v in voices:
        assert "voice_id" in v
        assert "name" in v
        assert "gender" in v
        assert "description" in v

    # 检查常见音色
    voice_ids = [v["voice_id"] for v in voices]
    assert "female-shaonv" in voice_ids
    assert "male-qn-qingse" in voice_ids
    assert "presenter_male" in voice_ids

    print(f"[PASS] 音色列表包含 {len(voices)} 个音色")
    for v in voices:
        print(f"  {v['voice_id']} - {v['name']}")


def test_models_list():
    """测试模型列表"""
    print("\n" + "=" * 60)
    print("测试 3: 模型列表")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    assert "speech-01" in MinimaxTTS.MODELS
    assert "speech-02" in MinimaxTTS.MODELS
    assert len(MinimaxTTS.MODELS) == 2

    print(f"[PASS] 支持 {len(MinimaxTTS.MODELS)} 个模型: {MinimaxTTS.MODELS}")


def test_api_key_required():
    """测试未提供 API Key 时抛出异常"""
    print("\n" + "=" * 60)
    print("测试 4: API Key 验证")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    # 需要清除可能存在的环境变量
    old_key = os.environ.pop("MINIMAX_API_KEY", None)
    try:
        import importlib
        import env as env_module

        importlib.reload(env_module)

        try:
            MinimaxTTS(api_key="")
            print("[FAIL] 应该抛出 ValueError")
            return
        except ValueError as e:
            assert "API Key" in str(e)
            print(f"[PASS] API Key 为空时正确抛出 ValueError: {e}")
    finally:
        if old_key:
            os.environ["MINIMAX_API_KEY"] = old_key
        import importlib
        import env as env_module

        importlib.reload(env_module)


def test_invalid_model():
    """测试无效模型抛出异常"""
    print("\n" + "=" * 60)
    print("测试 5: 无效模型验证")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    try:
        MinimaxTTS(api_key="test_key_123", model="invalid-model")
        print("[FAIL] 应该抛出 ValueError")
    except ValueError as e:
        assert "无效模型" in str(e)
        print(f"[PASS] 无效模型时正确抛出 ValueError: {e}")


def test_build_request_body():
    """测试 API 请求体构建"""
    print("\n" + "=" * 60)
    print("测试 6: API 请求体构建")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    tts = MinimaxTTS(
        api_key="test_key_123",
        model="speech-01",
        voice_id="female-shaonv",
        speed=1.0,
        volume=1.0,
        pitch=0,
        sample_rate=32000,
        bitrate=128000,
        audio_format="mp3",
    )

    test_text = "你好世界"
    body = tts._build_request_body(test_text)

    assert body["model"] == "speech-01"
    assert body["text"] == "你好世界"
    assert body["stream"] is False
    assert body["voice_setting"]["voice_id"] == "female-shaonv"
    assert body["voice_setting"]["speed"] == 1.0
    assert body["voice_setting"]["vol"] == 1.0
    assert body["voice_setting"]["pitch"] == 0
    assert body["audio_setting"]["sample_rate"] == 32000
    assert body["audio_setting"]["bitrate"] == 128000
    assert body["audio_setting"]["format"] == "mp3"

    print(f"[PASS] 请求体构建正确")
    print(f"  model: {body['model']}")
    print(f"  voice_id: {body['voice_setting']['voice_id']}")
    print(f"  text length: {len(body['text'])} chars")


def test_decimal_audio_decode():
    """测试十六进制音频数据解码"""
    print("\n" + "=" * 60)
    print("测试 7: 十六进制音频解码")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    tts = MinimaxTTS(
        api_key="test_key_123",
        voice_id="female-shaonv",
    )

    # 模拟 Minimax API 返回的十六进制音频
    test_hex = "52494646"  # "RIFF" 的十六进制表示
    decoded = tts._decode_audio(test_hex)
    assert decoded == b"RIFF", f"expected b'RIFF', got {decoded}"

    # 测试空字符串
    empty = tts._decode_audio("")
    assert empty == b""

    print(f"[PASS] 十六进制解码正确: {test_hex!r} -> {decoded!r}")


def test_factory_function():
    """测试工厂函数"""
    print("\n" + "=" * 60)
    print("测试 8: 工厂函数")
    print("=" * 60)

    from tts.minimax_tts import create_minimax_tts

    # 未配置 API key 应返回 None
    old_key = os.environ.pop("MINIMAX_API_KEY", None)
    try:
        import importlib
        import env as env_module

        importlib.reload(env_module)

        result = create_minimax_tts()
        assert result is None, "没有 API Key 时工厂函数应返回 None"
        print("[PASS] 未配置 API Key 时工厂函数返回 None")
    finally:
        if old_key:
            os.environ["MINIMAX_API_KEY"] = old_key
        import importlib
        import env as env_module

        importlib.reload(env_module)


def test_text_to_speech_empty():
    """测试空文本处理"""
    print("\n" + "=" * 60)
    print("测试 9: 空文本输入处理")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    tts = MinimaxTTS(
        api_key="test_key_123",
        voice_id="female-shaonv",
    )

    # 空文本应返回 False
    result = tts.text_to_speech("", "unused.mp3")
    assert result is False, "空文本应返回 False"

    # 空白文本应返回 False
    result = tts.text_to_speech("   \n  ", "unused.mp3")
    assert result is False, "空白文本应返回 False"

    print("[PASS] 空文本处理正确")


def test_custom_parameters():
    """测试自定义参数"""
    print("\n" + "=" * 60)
    print("测试 10: 自定义参数")
    print("=" * 60)

    from tts.minimax_tts import MinimaxTTS

    tts = MinimaxTTS(
        api_key="test_key_123",
        model="speech-02",
        voice_id="presenter_male",
        speed=0.8,
        volume=0.9,
        pitch=3,
        sample_rate=44100,
        bitrate=256000,
        audio_format="wav",
    )

    assert tts.model == "speech-02"
    assert tts.voice_id == "presenter_male"
    assert tts.speed == 0.8
    assert tts.volume == 0.9
    assert tts.pitch == 3
    assert tts.sample_rate == 44100
    assert tts.bitrate == 256000
    assert tts.audio_format == "wav"

    print("[PASS] 自定义参数全部生效")


def run_all_tests():
    print("\n" + "=" * 60)
    print("Minimax TTS 引擎测试套件")
    print("=" * 60)

    results = []

    test_funcs = [
        test_module_import,
        test_voice_list,
        test_models_list,
        test_api_key_required,
        test_invalid_model,
        test_build_request_body,
        test_decimal_audio_decode,
        test_factory_function,
        test_text_to_speech_empty,
        test_custom_parameters,
    ]

    for func in test_funcs:
        try:
            func()
            results.append((func.__doc__.strip().split("\n")[0], True))
        except Exception as e:
            print(f"[FAIL] 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((func.__doc__.strip().split("\n")[0], False))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    for name, result in results:
        print(f"  {name}: {'[PASS] 通过' if result else '[FAIL] 失败'}")

    print(f"\n总计: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
