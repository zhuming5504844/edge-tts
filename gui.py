"""edge-tts 图形界面：文本转语音（GUI 版）。"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from queue import Empty, Queue
from tkinter import BOTH, END, LEFT, RIGHT, W, X, filedialog, messagebox, ttk
import tkinter as tk

from edge_tts import Communicate, SubMaker, list_voices


class EdgeTTSGui:
    """基于 tkinter 的 edge-tts 图形界面。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("edge-tts 文本转语音")
        self.root.geometry("980x680")
        self.root.minsize(860, 620)

        self.voice_options: list[str] = []
        self.filtered_voice_options: list[str] = []
        self.worker_thread: threading.Thread | None = None
        self.event_queue: Queue[tuple[str, str]] = Queue()

        self._build_layout()
        self._set_default_values()
        self._load_voices_async()
        self.root.after(120, self._poll_queue)

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=BOTH, expand=True)

        top_frame = ttk.LabelFrame(main, text="参数设置", padding=10)
        top_frame.pack(fill=X, pady=(0, 10))

        self.voice_search_var = tk.StringVar()
        self.voice_var = tk.StringVar()
        self.rate_var = tk.StringVar()
        self.volume_var = tk.StringVar()
        self.pitch_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.subtitle_file_var = tk.StringVar()
        self.proxy_var = tk.StringVar()
        self.save_subtitle_var = tk.BooleanVar(value=True)

        ttk.Label(top_frame, text="语音筛选").grid(row=0, column=0, sticky=W, padx=(0, 8), pady=5)
        search_entry = ttk.Entry(top_frame, textvariable=self.voice_search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=5)
        search_entry.bind("<KeyRelease>", self._on_voice_filter_changed)

        ttk.Label(top_frame, text="语音角色").grid(row=0, column=2, sticky=W, padx=(0, 8), pady=5)
        self.voice_combo = ttk.Combobox(top_frame, textvariable=self.voice_var, state="readonly", height=16)
        self.voice_combo.grid(row=0, column=3, sticky="ew", pady=5)

        ttk.Label(top_frame, text="语速").grid(row=1, column=0, sticky=W, padx=(0, 8), pady=5)
        ttk.Entry(top_frame, textvariable=self.rate_var, width=12).grid(row=1, column=1, sticky=W, padx=(0, 8), pady=5)

        ttk.Label(top_frame, text="音量").grid(row=1, column=2, sticky=W, padx=(0, 8), pady=5)
        ttk.Entry(top_frame, textvariable=self.volume_var, width=12).grid(row=1, column=3, sticky=W, pady=5)

        ttk.Label(top_frame, text="音高").grid(row=2, column=0, sticky=W, padx=(0, 8), pady=5)
        ttk.Entry(top_frame, textvariable=self.pitch_var, width=12).grid(row=2, column=1, sticky=W, padx=(0, 8), pady=5)

        ttk.Label(top_frame, text="代理 (可选)").grid(row=2, column=2, sticky=W, padx=(0, 8), pady=5)
        ttk.Entry(top_frame, textvariable=self.proxy_var).grid(row=2, column=3, sticky="ew", pady=5)

        ttk.Label(top_frame, text="音频输出").grid(row=3, column=0, sticky=W, padx=(0, 8), pady=5)
        ttk.Entry(top_frame, textvariable=self.output_file_var).grid(row=3, column=1, columnspan=2, sticky="ew", padx=(0, 8), pady=5)
        ttk.Button(top_frame, text="选择", command=self._choose_audio_file).grid(row=3, column=3, sticky=W, pady=5)

        subtitle_row = ttk.Frame(top_frame)
        subtitle_row.grid(row=4, column=0, columnspan=4, sticky="ew", pady=5)
        subtitle_row.columnconfigure(2, weight=1)

        ttk.Checkbutton(subtitle_row, text="生成字幕 (.srt)", variable=self.save_subtitle_var, command=self._toggle_subtitle_state).pack(side=LEFT)
        ttk.Label(subtitle_row, text="字幕输出").pack(side=LEFT, padx=(16, 8))
        self.subtitle_entry = ttk.Entry(subtitle_row, textvariable=self.subtitle_file_var)
        self.subtitle_entry.pack(side=LEFT, fill=X, expand=True)
        self.subtitle_btn = ttk.Button(subtitle_row, text="选择", command=self._choose_subtitle_file)
        self.subtitle_btn.pack(side=LEFT, padx=(8, 0))

        for c in (1, 3):
            top_frame.columnconfigure(c, weight=1)

        text_frame = ttk.LabelFrame(main, text="输入文本", padding=10)
        text_frame.pack(fill=BOTH, expand=True)

        self.text_widget = tk.Text(text_frame, wrap="word", height=16)
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=text_scroll.set)
        self.text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        text_scroll.pack(side=RIGHT, fill="y")

        bottom = ttk.Frame(main)
        bottom.pack(fill=X, pady=(10, 0))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(bottom, textvariable=self.status_var).pack(side=LEFT, padx=(0, 12))

        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=180)
        self.progress.pack(side=LEFT)

        self.generate_btn = ttk.Button(bottom, text="开始合成", command=self._on_generate_clicked)
        self.generate_btn.pack(side=RIGHT)

    def _set_default_values(self) -> None:
        self.rate_var.set("+0%")
        self.volume_var.set("+0%")
        self.pitch_var.set("+0Hz")
        self.output_file_var.set(str(Path.cwd() / "output.mp3"))
        self.subtitle_file_var.set(str(Path.cwd() / "output.srt"))
        self.text_widget.insert(
            END,
            "欢迎使用 edge-tts 图形界面。\n"
            "请输入要转换的文本，选择语音和输出路径后点击“开始合成”。",
        )
        self._toggle_subtitle_state()

    def _toggle_subtitle_state(self) -> None:
        state = "normal" if self.save_subtitle_var.get() else "disabled"
        self.subtitle_entry.configure(state=state)
        self.subtitle_btn.configure(state=state)

    def _choose_audio_file(self) -> None:
        file_path = filedialog.asksaveasfilename(
            title="选择音频输出文件",
            defaultextension=".mp3",
            filetypes=[("MP3 文件", "*.mp3"), ("所有文件", "*.*")],
        )
        if file_path:
            self.output_file_var.set(file_path)

    def _choose_subtitle_file(self) -> None:
        file_path = filedialog.asksaveasfilename(
            title="选择字幕输出文件",
            defaultextension=".srt",
            filetypes=[("SRT 字幕", "*.srt"), ("所有文件", "*.*")],
        )
        if file_path:
            self.subtitle_file_var.set(file_path)

    def _load_voices_async(self) -> None:
        self.status_var.set("正在加载语音列表...")
        self.progress.start(12)

        def _worker() -> None:
            try:
                voices = asyncio.run(list_voices())
                items = sorted(v["ShortName"] for v in voices)
                self.event_queue.put(("voices_ok", "\n".join(items)))
            except Exception as exc:  # pylint: disable=broad-except
                self.event_queue.put(("voices_err", str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_voice_filter_changed(self, _event: object | None = None) -> None:
        keyword = self.voice_search_var.get().strip().lower()
        if keyword:
            filtered = [v for v in self.voice_options if keyword in v.lower()]
        else:
            filtered = list(self.voice_options)

        self.filtered_voice_options = filtered
        self.voice_combo["values"] = filtered

        current = self.voice_var.get()
        if current not in filtered and filtered:
            self.voice_var.set(filtered[0])

    def _on_generate_clicked(self) -> None:
        if self.worker_thread is not None and self.worker_thread.is_alive():
            messagebox.showwarning("请稍候", "当前仍在合成中，请等待完成。")
            return

        text = self.text_widget.get("1.0", END).strip()
        if not text:
            messagebox.showerror("输入为空", "请输入需要合成的文本。")
            return

        voice = self.voice_var.get().strip()
        if not voice:
            messagebox.showerror("语音未选择", "请先等待语音列表加载完成并选择语音。")
            return

        audio_path = Path(self.output_file_var.get().strip())
        if not audio_path.name:
            messagebox.showerror("路径错误", "请设置有效的音频输出路径。")
            return

        sub_path = None
        if self.save_subtitle_var.get():
            subtitle_text = self.subtitle_file_var.get().strip()
            if not subtitle_text:
                messagebox.showerror("路径错误", "已勾选字幕，请设置字幕输出路径。")
                return
            sub_path = Path(subtitle_text)

        self.generate_btn.configure(state="disabled")
        self.status_var.set("正在合成，请稍候...")
        self.progress.start(12)

        payload = {
            "text": text,
            "voice": voice,
            "rate": self.rate_var.get().strip() or "+0%",
            "volume": self.volume_var.get().strip() or "+0%",
            "pitch": self.pitch_var.get().strip() or "+0Hz",
            "proxy": self.proxy_var.get().strip() or None,
            "audio_path": audio_path,
            "subtitle_path": sub_path,
        }

        def _worker() -> None:
            try:
                asyncio.run(self._synthesize(payload))
                self.event_queue.put(("tts_ok", f"合成完成：{audio_path}"))
            except Exception as exc:  # pylint: disable=broad-except
                self.event_queue.put(("tts_err", str(exc)))

        self.worker_thread = threading.Thread(target=_worker, daemon=True)
        self.worker_thread.start()

    async def _synthesize(self, payload: dict[str, object]) -> None:
        communicate = Communicate(
            payload["text"],
            payload["voice"],
            rate=payload["rate"],
            volume=payload["volume"],
            pitch=payload["pitch"],
            proxy=payload["proxy"],
        )
        submaker = SubMaker()

        audio_path: Path = payload["audio_path"]
        subtitle_path: Path | None = payload["subtitle_path"]
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        if subtitle_path is not None:
            subtitle_path.parent.mkdir(parents=True, exist_ok=True)

        with audio_path.open("wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    submaker.feed(chunk)

        if subtitle_path is not None:
            subtitle_path.write_text(submaker.get_srt(), encoding="utf-8")

    def _poll_queue(self) -> None:
        try:
            while True:
                event, payload = self.event_queue.get_nowait()
                if event == "voices_ok":
                    self.voice_options = [v for v in payload.splitlines() if v]
                    self._on_voice_filter_changed()
                    if self.filtered_voice_options:
                        self.voice_var.set(self.filtered_voice_options[0])
                    self.status_var.set(f"语音加载完成，共 {len(self.voice_options)} 个")
                    self.progress.stop()
                elif event == "voices_err":
                    self.status_var.set("语音加载失败")
                    self.progress.stop()
                    messagebox.showerror("加载语音失败", payload)
                elif event == "tts_ok":
                    self.status_var.set(payload)
                    self.progress.stop()
                    self.generate_btn.configure(state="normal")
                    messagebox.showinfo("完成", payload)
                elif event == "tts_err":
                    self.status_var.set("合成失败")
                    self.progress.stop()
                    self.generate_btn.configure(state="normal")
                    messagebox.showerror("合成失败", payload)
        except Empty:
            pass
        finally:
            self.root.after(120, self._poll_queue)


def main() -> None:
    root = tk.Tk()
    ttk.Style(root).theme_use("clam")
    app = EdgeTTSGui(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
