#!/usr/bin/env python3
"""edge-tts 图形界面工具（无需命令行）。"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from tkinter import END, StringVar, Tk, filedialog, messagebox, ttk
import tkinter as tk

import edge_tts

DEFAULT_TEXT = "请输入你要转换的文本。"
DEFAULT_RATE = "+0%"
DEFAULT_PITCH = "+0Hz"
DEFAULT_VOLUME = "+0%"
DEFAULT_OUTPUT = "output.mp3"


class EdgeTTSGui:
    """基于 tkinter 的文本转语音 GUI。"""

    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Edge TTS 图形界面")
        self.root.geometry("980x700")
        self.root.minsize(900, 640)

        self.voice_var = StringVar()
        self.filter_var = StringVar()
        self.rate_var = StringVar(value=DEFAULT_RATE)
        self.pitch_var = StringVar(value=DEFAULT_PITCH)
        self.volume_var = StringVar(value=DEFAULT_VOLUME)
        self.status_var = StringVar(value="准备就绪")
        self.output_var = StringVar(value=str(Path.cwd() / DEFAULT_OUTPUT))
        self.subtitle_var = tk.BooleanVar(value=False)

        self._all_voices: list[dict] = []

        self._build_layout()
        self._load_voices()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        voice_frame = ttk.LabelFrame(main, text="语音选择", padding=10)
        voice_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        voice_frame.columnconfigure(1, weight=1)

        ttk.Label(voice_frame, text="搜索语音:").grid(row=0, column=0, sticky="w")
        filter_entry = ttk.Entry(voice_frame, textvariable=self.filter_var)
        filter_entry.grid(row=0, column=1, sticky="ew", padx=6)
        filter_entry.bind("<KeyRelease>", self._on_filter_changed)

        ttk.Button(voice_frame, text="刷新语音列表", command=self._load_voices).grid(
            row=0, column=2, sticky="e"
        )

        ttk.Label(voice_frame, text="语音:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, state="readonly")
        self.voice_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=(8, 0))

        output_frame = ttk.LabelFrame(main, text="输出配置", padding=10)
        output_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="输出音频:").grid(row=0, column=0, sticky="w")
        ttk.Entry(output_frame, textvariable=self.output_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(output_frame, text="浏览", command=self._choose_output).grid(row=0, column=2)
        ttk.Checkbutton(output_frame, text="同时导出字幕(.jsonl)", variable=self.subtitle_var).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        prosody_frame = ttk.LabelFrame(main, text="发音参数", padding=10)
        prosody_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        prosody_frame.columnconfigure(1, weight=1)

        self._build_slider(
            parent=prosody_frame,
            row=0,
            label="语速(%)",
            minimum=-50,
            maximum=100,
            var=self.rate_var,
            suffix="%",
        )
        self._build_slider(
            parent=prosody_frame,
            row=1,
            label="音调(Hz)",
            minimum=-100,
            maximum=100,
            var=self.pitch_var,
            suffix="Hz",
        )
        self._build_slider(
            parent=prosody_frame,
            row=2,
            label="音量(%)",
            minimum=-50,
            maximum=100,
            var=self.volume_var,
            suffix="%",
        )

        text_frame = ttk.LabelFrame(main, text="文本内容", padding=10)
        text_frame.grid(row=4, column=0, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        self.textbox = tk.Text(text_frame, wrap="word", font=("Microsoft YaHei UI", 11))
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.insert(END, DEFAULT_TEXT)

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.textbox.yview)
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.textbox.configure(yscrollcommand=text_scroll.set)

        action_frame = ttk.Frame(main)
        action_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        action_frame.columnconfigure(0, weight=1)

        ttk.Label(action_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        self.convert_btn = ttk.Button(action_frame, text="开始合成", command=self._start_convert)
        self.convert_btn.grid(row=0, column=1, padx=6)
        ttk.Button(action_frame, text="清空文本", command=self._clear_text).grid(row=0, column=2)

    def _build_slider(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        minimum: int,
        maximum: int,
        var: StringVar,
        suffix: str,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")

        slider = ttk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            command=lambda value, target=var, suf=suffix: target.set(
                self._format_value(float(value), suf)
            ),
        )
        slider.grid(row=row, column=1, sticky="ew", padx=6)

        current = self._parse_value(var.get())
        slider.set(current)

        entry = ttk.Entry(parent, textvariable=var, width=10)
        entry.grid(row=row, column=2, sticky="e")

    @staticmethod
    def _parse_value(raw: str) -> int:
        cleaned = raw.replace("+", "").replace("%", "").replace("Hz", "").strip()
        try:
            return int(cleaned)
        except ValueError:
            return 0

    @staticmethod
    def _format_value(value: float, suffix: str) -> str:
        integer = int(round(value))
        sign = "+" if integer >= 0 else ""
        return f"{sign}{integer}{suffix}"

    def _clear_text(self) -> None:
        self.textbox.delete("1.0", END)

    def _choose_output(self) -> None:
        output = filedialog.asksaveasfilename(
            title="选择输出音频文件",
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3"), ("All Files", "*.*")],
        )
        if output:
            self.output_var.set(output)

    def _load_voices(self) -> None:
        self._set_status("正在加载语音列表...")
        self.convert_btn.config(state="disabled")
        threading.Thread(target=self._load_voices_worker, daemon=True).start()

    def _load_voices_worker(self) -> None:
        try:
            voices = edge_tts.list_voices_sync()
            self._all_voices = sorted(voices, key=lambda v: v["ShortName"])
            self.root.after(0, self._refresh_voice_combobox)
        except Exception as exc:  # pragma: no cover
            self.root.after(0, lambda: messagebox.showerror("加载失败", str(exc)))
            self.root.after(0, lambda: self._set_status("语音列表加载失败"))
            self.root.after(0, lambda: self.convert_btn.config(state="normal"))

    def _refresh_voice_combobox(self) -> None:
        keyword = self.filter_var.get().strip().lower()
        filtered = self._all_voices
        if keyword:
            filtered = [
                voice
                for voice in self._all_voices
                if keyword in voice["ShortName"].lower()
                or keyword in voice["Locale"].lower()
                or keyword in voice.get("FriendlyName", "").lower()
            ]

        values = [f"{v['ShortName']} ({v['Locale']})" for v in filtered]
        self.voice_combo["values"] = values

        if values:
            if self.voice_var.get() not in values:
                self.voice_var.set(values[0])
            self._set_status(f"已加载语音 {len(values)} 个")
        else:
            self.voice_var.set("")
            self._set_status("没有匹配语音")

        self.convert_btn.config(state="normal")

    def _on_filter_changed(self, _event: object) -> None:
        self._refresh_voice_combobox()

    def _start_convert(self) -> None:
        text = self.textbox.get("1.0", END).strip()
        if not text:
            messagebox.showwarning("提示", "请输入要转换的文本")
            return

        if not self.voice_var.get():
            messagebox.showwarning("提示", "请先选择语音")
            return

        output_path = Path(self.output_var.get()).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        short_name = self.voice_var.get().split(" ", 1)[0]
        rate = self._validate_prosody(self.rate_var.get(), "%")
        pitch = self._validate_prosody(self.pitch_var.get(), "Hz")
        volume = self._validate_prosody(self.volume_var.get(), "%")

        self.convert_btn.config(state="disabled")
        self._set_status("正在合成音频，请稍候...")
        threading.Thread(
            target=self._convert_worker,
            kwargs={
                "text": text,
                "short_name": short_name,
                "output_path": output_path,
                "rate": rate,
                "pitch": pitch,
                "volume": volume,
            },
            daemon=True,
        ).start()

    def _validate_prosody(self, raw: str, suffix: str) -> str:
        value = self._parse_value(raw)
        sign = "+" if value >= 0 else ""
        return f"{sign}{value}{suffix}"

    def _convert_worker(
        self,
        text: str,
        short_name: str,
        output_path: Path,
        rate: str,
        pitch: str,
        volume: str,
    ) -> None:
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=short_name,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
            subtitle_path = str(output_path.with_suffix(".jsonl")) if self.subtitle_var.get() else None
            communicate.save_sync(str(output_path), metadata_fname=subtitle_path)

            self.root.after(
                0,
                lambda: self._on_convert_success(
                    output_path=str(output_path), subtitle_path=subtitle_path
                ),
            )
        except Exception as exc:  # pragma: no cover
            self.root.after(0, lambda: self._on_convert_error(exc))

    def _on_convert_success(self, output_path: str, subtitle_path: str | None) -> None:
        msg = f"合成完成: {output_path}"
        if subtitle_path:
            msg += f"\n字幕文件: {subtitle_path}"
        self._set_status("合成成功")
        self.convert_btn.config(state="normal")
        messagebox.showinfo("完成", msg)

    def _on_convert_error(self, error: Exception) -> None:
        self._set_status("合成失败")
        self.convert_btn.config(state="normal")
        messagebox.showerror("错误", str(error))

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)


def main() -> None:
    root = Tk()
    app = EdgeTTSGui(root)
    root.update_idletasks()
    root.minsize(root.winfo_width(), root.winfo_height())
    root.mainloop()


if __name__ == "__main__":
    if os.name == "nt":
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    main()
