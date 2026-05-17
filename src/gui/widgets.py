"""
自定义控件
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Callable, Optional


class FileSelector(ttk.Frame):
    def __init__(self, parent, label: str, filetypes: list = None, **kwargs):
        super().__init__(parent, **kwargs)

        self.filetypes = filetypes or [("所有文件", "*.*")]
        self.file_path = tk.StringVar()

        ttk.Label(self, text=label).pack(side=tk.LEFT, padx=(0, 5))

        self.entry = ttk.Entry(self, textvariable=self.file_path, width=40)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.browse_btn = ttk.Button(self, text="浏览...", command=self._browse)
        self.browse_btn.pack(side=tk.LEFT)

    def _browse(self):
        file_path = filedialog.askopenfilename(filetypes=self.filetypes)
        if file_path:
            self.file_path.set(file_path)

    def get(self) -> str:
        return self.file_path.get()

    def set(self, value: str):
        self.file_path.set(value)


class DirectorySelector(ttk.Frame):
    def __init__(self, parent, label: str, **kwargs):
        super().__init__(parent, **kwargs)

        self.dir_path = tk.StringVar()

        ttk.Label(self, text=label).pack(side=tk.LEFT, padx=(0, 5))

        self.entry = ttk.Entry(self, textvariable=self.dir_path, width=40)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.browse_btn = ttk.Button(self, text="浏览...", command=self._browse)
        self.browse_btn.pack(side=tk.LEFT)

    def _browse(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.dir_path.set(dir_path)

    def get(self) -> str:
        return self.dir_path.get()

    def set(self, value: str):
        self.dir_path.set(value)


class ProgressBar(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress.pack(side=tk.LEFT, padx=5)

        self.label = ttk.Label(self, text="0%")
        self.label.pack(side=tk.LEFT)

    def set(self, value: float):
        self.progress_var.set(value)
        self.label.config(text=f"{value:.1f}%")

    def reset(self):
        self.progress_var.set(0)
        self.label.config(text="0%")


class LogDisplay(ttk.Frame):
    def __init__(self, parent, height: int = 10, **kwargs):
        super().__init__(parent, **kwargs)

        self.text = tk.Text(self, height=height, wrap=tk.WORD)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def log(self, message: str, level: str = "INFO"):
        tag = level.lower()
        self.text.insert(tk.END, f"[{level}] {message}\n", tag)
        self.text.see(tk.END)

    def clear(self):
        self.text.delete(1.0, tk.END)

    def info(self, message: str):
        self.log(message, "INFO")

    def error(self, message: str):
        self.log(message, "ERROR")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def success(self, message: str):
        self.log(message, "SUCCESS")


class StatusLabel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.status_var = tk.StringVar(value="就绪")
        self.label = ttk.Label(self, textvariable=self.status_var)
        self.label.pack(side=tk.LEFT)

    def set(self, text: str):
        self.status_var.set(text)

    def set_ready(self):
        self.set("就绪")

    def set_working(self, text: str = "处理中..."):
        self.set(text)

    def set_done(self, text: str = "完成"):
        self.set(text)
