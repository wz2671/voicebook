r"""
VoiceBook GUI 启动脚本

使用方法：
    python run_gui.py

或者从任意目录：
    python D:\CODE\voicebook\run_gui.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.gui.main_window import run_gui

if __name__ == "__main__":
    run_gui()
