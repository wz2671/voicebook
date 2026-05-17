"""
音频转换面板
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pathlib import Path
from typing import Optional

from .widgets import DirectorySelector, ProgressBar, LogDisplay, StatusLabel


class ConvertPanel(ttk.Frame):
    TTS_ENGINES = {
        "Edge-TTS (推荐)": "edge-tts",
        "ChatTTS (离线)": "chat-tts"
    }

    EDGE_TTS_VOICES = [
        ("zh-CN-XiaoxiaoNeural", "女声，自然流畅"),
        ("zh-CN-YunyangNeural", "男声，新闻播报风格"),
        ("zh-CN-YunxiNeural", "男声，年轻活泼"),
        ("zh-CN-XiaoyiNeural", "女声，温柔甜美"),
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.is_running = False
        self.cancel_flag = False
        self.converter = None

        self._create_widgets()
        self._layout_widgets()

    def _create_widgets(self):
        self.chapter_selector = DirectorySelector(
            self,
            label="章节目录:"
        )

        default_chapter_dir = Path(__file__).parent.parent.parent / "chapter"
        self.chapter_selector.set(str(default_chapter_dir))

        self.output_selector = DirectorySelector(
            self,
            label="输出目录:"
        )

        default_audio_dir = Path(__file__).parent.parent.parent / "audios"
        self.output_selector.set(str(default_audio_dir))

        self.engine_frame = ttk.LabelFrame(self, text="TTS设置")

        ttk.Label(self.engine_frame, text="TTS引擎:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.engine_var = tk.StringVar(value="Edge-TTS (推荐)")
        self.engine_combo = ttk.Combobox(
            self.engine_frame,
            textvariable=self.engine_var,
            values=list(self.TTS_ENGINES.keys()),
            state="readonly",
            width=30
        )
        self.engine_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine_change)

        ttk.Label(self.engine_frame, text="语音选择:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.voice_var = tk.StringVar(value="zh-CN-XiaoxiaoNeural")
        self.voice_combo = ttk.Combobox(
            self.engine_frame,
            textvariable=self.voice_var,
            values=[f"{v[0]} - {v[1]}" for v in self.EDGE_TTS_VOICES],
            state="readonly",
            width=30
        )
        self.voice_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.voice_combo.current(0)

        self.progress = ProgressBar(self)

        self.log_display = LogDisplay(self, height=12)

        self.btn_frame = ttk.Frame(self)
        self.start_btn = ttk.Button(
            self.btn_frame,
            text="开始转换",
            command=self._start_convert
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

        ttk.Label(self, text="章节转音频", font=('', 14, 'bold')).pack(pady=padding)

        self.chapter_selector.pack(fill=tk.X, padx=padding, pady=5)
        self.output_selector.pack(fill=tk.X, padx=padding, pady=5)

        self.engine_frame.pack(fill=tk.X, padx=padding, pady=5)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=padding)

        self.progress.pack(pady=5)

        self.log_display.pack(fill=tk.BOTH, expand=True, padx=padding, pady=5)

        self.btn_frame.pack(pady=5)
        self.status_label.pack(pady=5)

    def _on_engine_change(self, event=None):
        engine = self.TTS_ENGINES.get(self.engine_var.get())

        if engine == "edge-tts":
            self.voice_combo['values'] = [f"{v[0]} - {v[1]}" for v in self.EDGE_TTS_VOICES]
            self.voice_combo.current(0)
        elif engine == "chat-tts":
            self.voice_combo['values'] = ["ChatTTS默认语音"]
            self.voice_combo.current(0)

    def _start_convert(self):
        chapter_dir = self.chapter_selector.get()
        output_dir = self.output_selector.get()

        if not chapter_dir:
            messagebox.showerror("错误", "请选择章节目录")
            return

        if not Path(chapter_dir).exists():
            messagebox.showerror("错误", "章节目录不存在")
            return

        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        self.is_running = True
        self.cancel_flag = False
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.status_label.set_working("正在转换...")
        self.log_display.clear()

        engine = self.TTS_ENGINES.get(self.engine_var.get())
        voice = self.voice_var.get().split(" - ")[0] if " - " in self.voice_var.get() else "default"

        self.log_display.info(f"TTS引擎: {engine}")
        self.log_display.info(f"语音: {voice}")
        self.log_display.info(f"章节目录: {chapter_dir}")
        self.log_display.info(f"输出目录: {output_dir}")

        thread = threading.Thread(
            target=self._convert_thread,
            args=(chapter_dir, output_dir, engine, voice),
            daemon=True
        )
        thread.start()

    def _convert_thread(self, chapter_dir: str, output_dir: str, engine: str, voice: str):
        try:
            import sys
            libs_path = Path(__file__).parent.parent / "libs"
            if str(libs_path) not in sys.path:
                sys.path.insert(0, str(libs_path))

            chapter_path = Path(chapter_dir)
            book_name = chapter_path.name

            md_files = sorted(chapter_path.glob("chapter*.md"))

            if not md_files:
                self.log_display.error("未找到章节文件")
                self.status_label.set("错误: 未找到章节文件")
                self._on_finished()
                return

            total = len(md_files)
            self.log_display.info(f"找到 {total} 个章节文件")

            if engine == "edge-tts":
                self._convert_with_edge_tts(md_files, output_dir, book_name, voice)
            elif engine == "chat-tts":
                self._convert_with_chat_tts(md_files, output_dir, book_name)

        except Exception as e:
            self.log_display.error(f"转换失败: {str(e)}")
            self.status_label.set(f"错误: {str(e)}")
            self._on_finished()

    def _convert_with_edge_tts(self, md_files, output_dir: str, book_name: str, voice: str):
        try:
            from tts.audio_converter import AudioConverter

            converter = AudioConverter(voice=voice)
            total = len(md_files)
            success_count = 0

            for i, md_file in enumerate(md_files):
                if self.cancel_flag:
                    self._on_cancelled()
                    return

                progress = (i + 1) / total * 100
                self.progress.set(progress)
                self.log_display.info(f"转换 {i+1}/{total}: {md_file.name}")

                audio_path = Path(output_dir) / book_name / md_file.name.replace('.md', '.mp3')

                try:
                    if converter.convert_chapter(str(md_file), str(audio_path)):
                        success_count += 1
                        self.log_display.success(f"成功: {audio_path.name}")
                    else:
                        self.log_display.warning(f"失败: {md_file.name}")
                except Exception as e:
                    self.log_display.error(f"错误: {md_file.name} - {str(e)}")

            self.log_display.success(f"转换完成！成功: {success_count}/{total}")
            self.status_label.set_done(f"完成 ({success_count}/{total})")
            self._on_finished()

        except Exception as e:
            self.log_display.error(f"Edge-TTS转换失败: {str(e)}")
            self.status_label.set(f"错误: {str(e)}")
            self._on_finished()

    def _convert_with_chat_tts(self, md_files, output_dir: str, book_name: str):
        try:
            from tts.chat_tts_converter import ChatTTSConverter

            if not ChatTTSConverter.is_available():
                self.log_display.error("ChatTTS未安装，请运行: pip install ChatTTS torch torchaudio")
                self.status_label.set("错误: ChatTTS未安装")
                self._on_finished()
                return

            self.log_display.info("正在加载ChatTTS模型...")
            converter = ChatTTSConverter(use_gpu=True)

            if not converter.load_model():
                self.log_display.error("ChatTTS模型加载失败")
                self.status_label.set("错误: 模型加载失败")
                self._on_finished()
                return

            self.log_display.success("ChatTTS模型加载成功")

            total = len(md_files)
            success_count = 0

            for i, md_file in enumerate(md_files):
                if self.cancel_flag:
                    self._on_cancelled()
                    return

                progress = (i + 1) / total * 100
                self.progress.set(progress)
                self.log_display.info(f"转换 {i+1}/{total}: {md_file.name}")

                audio_path = Path(output_dir) / book_name / md_file.name.replace('.md', '.wav')

                try:
                    if converter.convert_chapter(str(md_file), str(audio_path)):
                        success_count += 1
                        self.log_display.success(f"成功: {audio_path.name}")
                    else:
                        self.log_display.warning(f"失败: {md_file.name}")
                except Exception as e:
                    self.log_display.error(f"错误: {md_file.name} - {str(e)}")

            self.log_display.success(f"转换完成！成功: {success_count}/{total}")
            self.status_label.set_done(f"完成 ({success_count}/{total})")
            self._on_finished()

        except Exception as e:
            self.log_display.error(f"ChatTTS转换失败: {str(e)}")
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
