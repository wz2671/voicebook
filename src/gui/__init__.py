"""
VoiceBook GUI 图形化界面
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.resolve()
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from .main_window import VoiceBookApp, run_gui

__all__ = ['VoiceBookApp', 'run_gui']
