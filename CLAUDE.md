# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoiceBook converts MOBI ebooks to audiobooks via TTS. It supports three TTS backends (Edge-TTS, ChatTTS, Minimax API) and provides both CLI and tkinter GUI interfaces.

## Commands

```bash
# CLI entry point
python -m src.main <command> [options]

# Commands: extract | convert | process | voices
python -m src.main extract books/mybook.mobi
python -m src.main convert chapter/mybook --engine edge-tts -v zh-CN-XiaoxiaoNeural
python -m src.main process books/mybook.mobi --engine minimax
python -m src.main voices

# GUI
python run_gui.py

# Tests (standalone scripts, no test framework)
python test/test_env_config.py
python test/test_minimax_tts.py
python test/test_chat_tts.py

# Install dependencies
pip install -r requirements.txt
# Optional: ChatTTS (needs ~2GB model download, torch)
pip install ChatTTS torch torchaudio
```

## Architecture

**Pipeline**: MOBI file → `mobi_handler/` extracts chapters as `.md` → `tts/` converts each `.md` to audio (mp3/wav)

### Directory layout

```
src/
  main.py            # CLI entry (argparse subcommands)
  config.py           # Project paths (BOOKS_DIR, CHAPTER_DIR, AUDIOS_DIR)
  env.py              # EnvConfig singleton - all config with priority: os.environ > .env.local > defaults
  mobi_handler/       # MOBI extraction → chapter*.md files
  tts/
    tts_engine.py     # Edge-TTS wrapper (Microsoft free TTS, async/sync)
    minimax_tts.py    # Minimax API TTS (HTTP POST, hex-encoded audio)
    chat_tts_converter.py  # ChatTTS local model (torch-based, GPU/CPU)
    audio_converter.py     # Higher-level converter (text splitting, ffmpeg merge) wrapping TTSEngine
  gui/                # tkinter GUI (Notebook with ExtractPanel + ConvertPanel)
  libs/               # Bundled third-party: mobi/, edge_tts/, chat_tts/
```

### TTS engine interface

All engines expose `text_to_speech(text: str, output_path: str) -> bool`. The CLI `main.py` switch-case selects engine, calls `text_to_speech`, and displays progress via `ProgressBar`. Edge-TTS uses a separate `text_to_speech_sync()` method internally but both ChatTTS and Minimax share the `text_to_speech` signature.

### Config system

`src/env.py` defines `EnvConfig` with properties for all settings (API keys, voice IDs, audio params). Import as `from env import env`. Actual values from `.env.local` in project root (gitignored). Priority: os.environ > `.env.local` > hardcoded defaults. ChatTTS env vars are auto-injected into `os.environ` on import.

### Code conventions

- Python with Chinese docstrings and comments (log messages are in Chinese)
- Logging: standard `logging` module for CLI; `loguru` imported but not widely used
- GUI runs blocking operations in `threading.Thread` (daemon) with cancel flags
- Tests are standalone scripts with print-based assertions, no pytest/unittest
- Path handling: `pathlib.Path` throughout; `sys.path.insert` used liberally to add `src/libs` to import path
