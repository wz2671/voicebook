import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

BOOKS_DIR = PROJECT_ROOT / "books"

CHAPTER_DIR = PROJECT_ROOT / "chapter"

AUDIOS_DIR = PROJECT_ROOT / "audios"

DOC_DIR = PROJECT_ROOT / "doc"

# 音频格式由 env.py 配置中心管理，此处作为后备
from env import env as _env

AUDIO_FORMAT = _env.audio_format


def ensure_dirs():
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    CHAPTER_DIR.mkdir(parents=True, exist_ok=True)
    AUDIOS_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
