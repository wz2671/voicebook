"""
VoiceBook 主窗口
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from .extract_panel import ExtractPanel
from .convert_panel import ConvertPanel


class VoiceBookApp:
    def __init__(self, root: tk.Tk = None):
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root

        self.root.title("VoiceBook - 电子书转音频工具")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        self._setup_style()
        self._create_widgets()
        self._layout_widgets()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')

    def _create_widgets(self):
        self.notebook = ttk.Notebook(self.root)

        self.extract_frame = ttk.Frame(self.notebook)
        self.convert_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.extract_frame, text="  MOBI提取  ")
        self.notebook.add(self.convert_frame, text="  音频转换  ")

        self.extract_panel = ExtractPanel(self.extract_frame)
        self.convert_panel = ConvertPanel(self.convert_frame)

        self.status_bar = ttk.Frame(self.root)
        self.status_label = ttk.Label(
            self.status_bar,
            text="VoiceBook v1.0 - 本地电子书转音频工具",
            relief=tk.SUNKEN
        )

    def _layout_widgets(self):
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.extract_panel.pack(fill=tk.BOTH, expand=True)
        self.convert_panel.pack(fill=tk.BOTH, expand=True)

        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def run(self):
        self.root.mainloop()


def run_gui():
    app = VoiceBookApp()
    app.run()


if __name__ == "__main__":
    run_gui()
