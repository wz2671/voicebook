"""
MOBI提取面板
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import shutil
from pathlib import Path

from .widgets import FileSelector, DirectorySelector, ProgressBar, LogDisplay, StatusLabel


class ExtractPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.is_running = False
        self.cancel_flag = False

        self._create_widgets()
        self._layout_widgets()

    def _create_widgets(self):
        self.file_selector = FileSelector(
            self,
            label="MOBI文件:",
            filetypes=[("MOBI文件", "*.mobi"), ("所有文件", "*.*")]
        )

        self.output_selector = DirectorySelector(
            self,
            label="输出目录:"
        )

        default_chapter_dir = Path(__file__).parent.parent.parent / "chapter"
        self.output_selector.set(str(default_chapter_dir))

        self.progress = ProgressBar(self)

        self.log_display = LogDisplay(self, height=15)

        self.btn_frame = ttk.Frame(self)
        self.start_btn = ttk.Button(
            self.btn_frame,
            text="开始提取",
            command=self._start_extract
        )
        self.cancel_btn = ttk.Button(
            self.btn_frame,
            text="取消",
            command=self._cancel,
            state=tk.DISABLED
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = StatusLabel(self)

    def _layout_widgets(self):
        padding = 10

        ttk.Label(self, text="MOBI章节提取", font=('', 14, 'bold')).pack(pady=padding)

        self.file_selector.pack(fill=tk.X, padx=padding, pady=5)
        self.output_selector.pack(fill=tk.X, padx=padding, pady=5)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=padding)

        self.progress.pack(pady=5)

        self.log_display.pack(fill=tk.BOTH, expand=True, padx=padding, pady=5)

        self.btn_frame.pack(pady=5)
        self.status_label.pack(pady=5)

    def _start_extract(self):
        mobi_path = self.file_selector.get()
        output_dir = self.output_selector.get()

        if not mobi_path:
            messagebox.showerror("错误", "请选择MOBI文件")
            return

        if not Path(mobi_path).exists():
            messagebox.showerror("错误", "MOBI文件不存在")
            return

        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        self.is_running = True
        self.cancel_flag = False
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.status_label.set_working("正在提取...")
        self.log_display.clear()
        self.log_display.info(f"开始提取: {mobi_path}")

        thread = threading.Thread(
            target=self._extract_thread,
            args=(mobi_path, output_dir),
            daemon=True
        )
        thread.start()

    def _extract_thread(self, mobi_path: str, output_dir: str):
        try:
            import sys
            libs_path = Path(__file__).parent.parent / "libs"
            if str(libs_path) not in sys.path:
                sys.path.insert(0, str(libs_path))

            from mobi_handler.mobi_extractor import process_mobi

            self.log_display.info("正在解析MOBI文件...")
            self.progress.set(10)

            if self.cancel_flag:
                self._on_cancelled()
                return

            saved_files, tempdir = process_mobi(mobi_path, output_dir)

            if self.cancel_flag:
                shutil.rmtree(tempdir, ignore_errors=True)
                self._on_cancelled()
                return

            total = len(saved_files)
            self.log_display.info(f"提取完成，共 {total} 个章节")

            for i, file_path in enumerate(saved_files):
                if self.cancel_flag:
                    shutil.rmtree(tempdir, ignore_errors=True)
                    self._on_cancelled()
                    return

                progress = 10 + (i + 1) / total * 80
                self.progress.set(progress)
                self.log_display.info(f"保存: {Path(file_path).name}")

            shutil.rmtree(tempdir, ignore_errors=True)

            self.progress.set(100)
            self.log_display.success(f"提取完成！共保存 {total} 个章节文件")
            self.status_label.set_done("提取完成")

            self._on_finished()

        except Exception as e:
            self.log_display.error(f"提取失败: {str(e)}")
            self.status_label.set(f"错误: {str(e)}")
            self._on_finished()

    def _cancel(self):
        self.cancel_flag = True
        self.log_display.warning("正在取消...")

    def _on_cancelled(self):
        self.log_display.warning("操作已取消")
        self.status_label.set("已取消")
        self._on_finished()

    def _on_finished(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
