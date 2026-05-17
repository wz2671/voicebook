"""
env.py / .env.local 配置系统单元测试

测试环境变量配置中心的加载、优先级、默认值等功能。
"""

import os
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_env_defaults():
    """测试 env.py 默认值"""
    print("=" * 60)
    print("测试 1: 默认值检查")
    print("=" * 60)

    from env import env

    # Minimax 默认值
    assert env.minimax_model == "speech-01", f"expected speech-01, got {env.minimax_model}"
    assert env.minimax_voice_id == "female-shaonv", f"expected female-shaonv, got {env.minimax_voice_id}"
    assert env.minimax_speed == 1.0
    assert env.minimax_volume == 1.0
    assert env.minimax_pitch == 0
    assert env.minimax_sample_rate == 32000
    assert env.minimax_bitrate == 128000
    assert env.minimax_audio_format == "mp3"

    # Edge TTS 默认值
    assert env.edge_tts_default_voice == "zh-CN-XiaoxiaoNeural"

    # ChatTTS 默认值
    assert env.chat_tts_use_gpu is True

    # 应用默认值
    assert env.audio_format == "mp3"
    assert env.log_level == "INFO"

    print("[PASS] 所有默认值检查通过")


def test_empty_api_key():
    """测试未配置 API Key 时返回空字符串"""
    print("\n" + "=" * 60)
    print("测试 2: 空 API Key 检查")
    print("=" * 60)

    # 清除可能存在的环境变量
    old_val = os.environ.pop("MINIMAX_API_KEY", None)
    try:
        import importlib
        import env as env_module

        importlib.reload(env_module)
        from env import env

        assert env.minimax_api_key == "", f"expected empty, got '{env.minimax_api_key}'"
        print("[PASS] 未配置时 API Key 返回空字符串")
    finally:
        if old_val:
            os.environ["MINIMAX_API_KEY"] = old_val
        import importlib
        import env as env_module

        importlib.reload(env_module)


def test_env_var_priority():
    """测试环境变量优先级 > .env.local"""
    print("\n" + "=" * 60)
    print("测试 3: 环境变量优先级")
    print("=" * 60)

    test_key = "TEST_MINIMAX_VOICE_xyz"
    test_value = "test-voice-override"
    os.environ[test_key] = test_value

    import env as env_module

    saved = {}
    for attr in dir(env_module):
        if attr.startswith("_") or attr in ("env",):
            continue
        saved[attr] = getattr(env_module, attr, None)

    import importlib

    importlib.reload(env_module)

    from env import _get

    result = _get(test_key, "default")
    assert result == test_value, f"env var should take priority: expected '{test_value}', got '{result}'"

    del os.environ[test_key]
    print("[PASS] 环境变量优先级正确")


def test_type_conversion():
    """测试数值类型转换"""
    print("\n" + "=" * 60)
    print("测试 4: 数值类型转换")
    print("=" * 60)

    from env import env

    assert isinstance(env.minimax_speed, float)
    assert isinstance(env.minimax_volume, float)
    assert isinstance(env.minimax_pitch, int)
    assert isinstance(env.minimax_sample_rate, int)
    assert isinstance(env.minimax_bitrate, int)
    assert isinstance(env.chat_tts_use_gpu, bool)

    print("[PASS] 类型转换全部正确")


def test_chat_tts_env_injection():
    """测试 ChatTTS 环境变量已注入到 os.environ"""
    print("\n" + "=" * 60)
    print("测试 5: ChatTTS 环境变量注入")
    print("=" * 60)

    assert os.environ.get("VLLM_USE_MODELSCOPE") == "False"
    assert os.environ.get("RAY_USAGE_STATS_ENABLED") == "0"
    assert os.environ.get("TORCH_NCCL_AVOID_RECORD_STREAMS") == "1"

    print("[PASS] ChatTTS 环境变量注入正确")


def run_all_tests():
    print("\n" + "=" * 60)
    print("env.py 配置系统测试套件")
    print("=" * 60)

    results = []

    try:
        test_env_defaults()
        results.append(("默认值检查", True))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        results.append(("默认值检查", False))

    try:
        test_empty_api_key()
        results.append(("空API Key检查", True))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        results.append(("空API Key检查", False))

    try:
        test_env_var_priority()
        results.append(("环境变量优先级", True))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        results.append(("环境变量优先级", False))

    try:
        test_type_conversion()
        results.append(("数值类型转换", True))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        results.append(("数值类型转换", False))

    try:
        test_chat_tts_env_injection()
        results.append(("ChatTTS环境变量注入", True))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        results.append(("ChatTTS环境变量注入", False))

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
