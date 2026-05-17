"""
音频转换面板
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pathlib import Path
from typing import Optional

from .widgets import DirectorySelector, ProgressBar, LogDisplay, StatusLabel
from tts.registry import TTSEngineRegistry


class ConvertPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.is_running = False
        self.cancel_flag = False
        self.converter = None

        self._create_widgets()
        self._layout_widgets()
        self._load_engines()

    def _load_engines(self):
        """从注册中心加载引擎列表和语音列表"""
        engine_map = TTSEngineRegistry.list_engines()
        if not engine_map:
            return

        self._engines = engine_map  # {id: display_name}
        self._engine_display_names = list(engine_map.values())
        self._engine_ids = list(engine_map.keys())

        # 设置引擎下拉框
        self.engine_combo['values'] = self._engine_display_names
        if self._engine_display_names:
            self.engine_combo.current(0)
            self._on_engine_change()

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
        self.engine_var = tk.StringVar()
        self.engine_combo = ttk.Combobox(
            self.engine_frame,
            textvariable=self.engine_var,
            state="readonly",
            width=30
        )
        self.engine_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine_change)

        ttk.Label(self.engine_frame, text="语音选择:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(
            self.engine_frame,
            textvariable=self.voice_var,
            state="readonly",
            width=30
        )
        self.voice_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

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

    def _get_current_engine_id(self) -> Optional[str]:
        """获取当前选中的引擎 ID"""
        display_name = self.engine_var.get()
        if not display_name or not hasattr(self, '_engines'):
            return None
        for eid, name in self._engines.items():
            if name == display_name:
                return eid
        return None

    def _on_engine_change(self, event=None):
        """引擎切换时更新语音列表"""
        engine_id = self._get_current_engine_id()
        if not engine_id:
            return

        voices = TTSEngineRegistry.get_voices(engine_id)
        if voices:
            voice_labels = [
                f"{v.get('voice_id', v.get('name', ''))} - {v.get('description', '')}"
                for v in voices
            ]
            self.voice_combo['values'] = voice_labels
            self.voice_combo.current(0)
        else:
            self.voice_combo['values'] = ["(无预设语音)"]
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

        engine_id = self._get_current_engine_id()
        if not engine_id:
            messagebox.showerror("错误", "未选择TTS引擎")
            return

        self.is_running = True
        self.cancel_flag = False
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.status_label.set_working("正在转换...")
        self.log_display.clear()

        voice_raw = self.voice_var.get()
        voice = voice_raw.split(" - ")[0] if " - " in voice_raw else "default"

        self.log_display.info(f"TTS引擎: {engine_id}")
        self.log_display.info(f"语音: {voice}")
        self.log_display.info(f"章节目录: {chapter_dir}")
        self.log_display.info(f"输出目录: {output_dir}")

        thread = threading.Thread(
            target=self._convert_thread,
            args=(chapter_dir, output_dir, engine_id, voice),
            daemon=True
        )
        thread.start()

    def _convert_thread(self, chapter_dir: str, output_dir: str, engine_id: str, voice: str):
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

            # 通过注册中心创建引擎
            try:
                tts = TTSEngineRegistry.create_engine(engine_id, voice=voice)
            except ValueError as e:
                self.log_display.error(f"引擎创建失败: {e}")
                self.status_label.set(f"错误: {e}")
                self._on_finished()
                return

            success_count = 0

            for i, md_file in enumerate(md_files):
                if self.cancel_flag:
                    self._on_cancelled()
                    return

                progress = (i + 1) / total * 100
                self.progress.set(progress)
                self.log_display.info(f"转换 {i+1}/{total}: {md_file.name}")

                # 读取章节内容
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = content.split('\n')
                text_content = '\n'.join(lines[1:]).strip() if lines and lines[0].startswith('# ') else content.strip()

                if not text_content:
                    self.log_display.warning(f"章节内容为空: {md_file.name}")
                    continue

                # 确定输出扩展名
                from env import env as _env
                audio_ext = _env.audio_format
                audio_path = Path(output_dir) / book_name / md_file.name.replace('.md', f'.{audio_ext}')

                try:
                    # Edge-TTS 使用同步方法
                    if engine_id == 'edge-tts':
                        success = tts.text_to_speech_sync(text_content, str(audio_path))
                    else:
                        success = tts.text_to_speech(text_content, str(audio_path))

                    if success:
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
            self.log_display.error(f"转换失败: {str(e)}")
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
