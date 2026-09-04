"""ANNE Embedded Tinker — lightweight in-process local AI launcher."""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.agent.local_memory import LocalMemory
from anne.agent.runtime import AnneAgent
from anne.providers.embedded import EmbeddedAIProvider
from anne.tools.web_research import WebResearchClient

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_CONTEXT_CHARS = 9_000
TEXT_EXTENSIONS = {
    ".txt", ".md", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".json",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".tsv", ".xml",
    ".html", ".css", ".sql", ".sh", ".bat", ".ps1", ".c", ".cpp", ".h",
    ".hpp", ".java", ".go", ".rs", ".swift", ".kt", ".log", ".tex",
}


class EmbeddedAnneTinker(tk.Tk):
    """Dedicated lightweight Tinker; never starts Ollama or a local server."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Embedded Tinker")
        self.geometry("1180x760")
        self.minsize(980, 620)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.attachments: list[Path] = []
        self.web_research = tk.BooleanVar(value=False)
        self._build_ui()
        self.refresh_status()
        self.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.LabelFrame(root, text="Embedded AI")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Engine").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(
            header,
            text="Qwen2.5-0.5B-Instruct GGUF • llama.cpp in-process • Ollama yok",
        ).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        self.model_status = ttk.Label(header, text="Model durumu kontrol ediliyor…")
        self.model_status.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(2, 2))
        self.download_button = ttk.Button(
            header, text="Modeli İndir / Yenile", command=self.download_model
        )
        self.download_button.grid(row=0, column=2, rowspan=2, padx=8, pady=6)

        self.progress = ttk.Progressbar(header, mode="determinate", maximum=100, length=360)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 2))
        self.progress_label = ttk.Label(header, text="0 MB / bekleniyor")
        self.progress_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 5))

        options = ttk.Frame(header)
        options.grid(row=2, column=2, rowspan=2, sticky="e", padx=8, pady=2)
        ttk.Checkbutton(
            options,
            text="İnternet araştırması (varsayılan kapalı)",
            variable=self.web_research,
        ).pack(anchor="e")
        ttk.Label(options, text="CPU: 2 thread • context: 2048 • max output: 256").pack(
            anchor="e", pady=(4, 0)
        )

        research = ttk.LabelFrame(root, text="Araştırma Dosyaları")
        research.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        research.columnconfigure(0, weight=1)
        self.file_list = tk.Listbox(research, height=4, selectmode="extended")
        self.file_list.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        buttons = ttk.Frame(research)
        buttons.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        ttk.Button(buttons, text="Dosya Ekle", command=self.add_files).pack(fill="x", pady=(0, 4))
        ttk.Button(buttons, text="Seçileni Sil", command=self.remove_selected_files).pack(fill="x", pady=4)
        ttk.Button(buttons, text="Temizle", command=self.clear_files).pack(fill="x", pady=4)
        ttk.Label(
            research,
            text="TXT / MD / kod / JSON / CSV / PDF / DOCX • modele yalnızca küçük bağlam gönderilir",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        chat_frame = ttk.LabelFrame(root, text="ANNE")
        chat_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        self.chat = scrolledtext.ScrolledText(chat_frame, wrap="word", font=("Segoe UI", 10))
        self.chat.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.chat.configure(state="disabled")

        input_frame = ttk.Frame(root)
        input_frame.grid(row=3, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        self.input_box = tk.Text(input_frame, height=4, wrap="word", font=("Segoe UI", 10))
        self.input_box.grid(row=0, column=0, sticky="ew")
        self.input_box.bind("<Control-Return>", lambda _event: self.send())
        action = ttk.Frame(input_frame)
        action.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        ttk.Button(action, text="Gönder", command=self.send).pack(fill="x", pady=(0, 5))
        ttk.Button(action, text="Temizle", command=lambda: self.input_box.delete("1.0", "end")).pack(fill="x")
        self.status = ttk.Label(root, text="Hazır", anchor="w")
        self.status.grid(row=4, column=0, sticky="ew", pady=(5, 0))

    def _model_paths(self) -> tuple[Path, Path]:
        target = EmbeddedAIProvider.default_model_path()
        return target, target.with_suffix(target.suffix + ".part")

    @staticmethod
    def _format_size(size: int) -> str:
        return f"{size / (1024 * 1024):.1f} MB"

    def refresh_status(self) -> None:
        provider = EmbeddedAIProvider()
        _target, partial = self._model_paths()
        if provider.is_installed():
            size_mb = provider.model_path.stat().st_size / (1024 * 1024)
            self.model_status.configure(text=f"Model hazır • {size_mb:.0f} MB")
            self.progress.stop()
            self.progress.configure(mode="determinate", value=100)
            self.progress_label.configure(text=f"{size_mb:.1f} MB • tamamlandı")
            self.download_button.configure(text="Modeli Yenile", state="normal")
            return
        if partial.exists() and partial.stat().st_size > 0:
            self.model_status.configure(text="Kısmi model dosyası bulundu • indirme yeniden başlatılabilir")
            self.progress.stop()
            self.progress.configure(mode="determinate", value=0)
            self.progress_label.configure(text=f"{self._format_size(partial.stat().st_size)} • kısmi")
        else:
            self.model_status.configure(text="Model henüz indirilmedi")
            self.progress.stop()
            self.progress.configure(mode="determinate", value=0)
            self.progress_label.configure(text="0 MB / bekleniyor")
        self.download_button.configure(text="Modeli İndir / Yenile", state="normal")

    def _queue_model_progress(self, received: int, total: int) -> None:
        self.result_queue.put(("model_progress", (received, total)))

    def download_model(self) -> None:
        if str(self.download_button.cget("state")) == "disabled":
            return
        self.download_button.configure(state="disabled", text="İndiriliyor…")
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.progress_label.configure(text="0 MB / hazırlanıyor…")
        self.model_status.configure(text="Model indiriliyor…")

        def worker() -> None:
            try:
                EmbeddedAIProvider.download_default_model(progress=self._queue_model_progress)
                self.result_queue.put(("model", "Model download complete"))
            except Exception as exc:
                self.result_queue.put(("download_error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Araştırma dosyaları",
            filetypes=[
                (
                    "Research files",
                    "*.txt *.md *.rst *.py *.js *.ts *.json *.yaml *.yml *.toml *.csv *.tsv *.xml *.html *.css *.sql *.pdf *.docx",
                ),
                ("All files", "*.*"),
            ],
        )
        for raw in paths:
            path = Path(raw)
            if path not in self.attachments:
                self.attachments.append(path)
                self.file_list.insert("end", str(path))
        self.status.configure(text=f"Araştırma dosyası: {len(self.attachments)}")

    def remove_selected_files(self) -> None:
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
            self.attachments.pop(index)

    def clear_files(self) -> None:
        self.attachments.clear()
        self.file_list.delete(0, "end")

    @staticmethod
    def _extract_docx(path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs: list[str] = []
        for paragraph in root.iter(f"{ns}p"):
            line = "".join(node.text or "" for node in paragraph.iter(f"{ns}t")).strip()
            if line:
                paragraphs.append(line)
        return "\n".join(paragraphs)

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        from pypdf import PdfReader
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)

    @classmethod
    def _read_attachment(cls, path: Path) -> str:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"{path.name} 4 MB sınırını aşıyor")
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return cls._extract_pdf(path)
        if suffix == ".docx":
            return cls._extract_docx(path)
        if suffix not in TEXT_EXTENSIONS:
            raise ValueError(f"Desteklenmeyen dosya türü: {suffix or '(uzantı yok)'}")
        return path.read_text(encoding="utf-8", errors="replace")

    def _build_context(self) -> str:
        parts: list[str] = []
        remaining = MAX_CONTEXT_CHARS
        for path in self.attachments:
            text = self._read_attachment(path).strip()
            if not text:
                continue
            chunk = f"===== RESEARCH FILE: {path.name} =====\n{text}"[:remaining]
            parts.append(chunk)
            remaining -= len(chunk)
            if remaining <= 0:
                break
        return "\n\n".join(parts)

    def send(self) -> None:
        user_input = self.input_box.get("1.0", "end").strip()
        if not user_input:
            return
        try:
            external_context = self._build_context()
        except Exception as exc:
            messagebox.showwarning("ANNE Embedded Tinker", str(exc))
            return
        self.input_box.delete("1.0", "end")
        self._append("YOU", user_input)
        self.status.configure(text="ANNE hazırlanıyor…")
        threading.Thread(target=self._worker, args=(user_input, external_context), daemon=True).start()

    def _worker(self, user_input: str, external_context: str) -> None:
        try:
            if self.web_research.get():
                self.result_queue.put(("status", "Web araştırması yapılıyor…"))
                try:
                    results = WebResearchClient().search(user_input, max_results=4)
                    external_context = WebResearchClient.format_results(results) + "\n\n" + external_context
                    self.result_queue.put(("web", results))
                except Exception as exc:
                    external_context += f"\n\n===== WEB RESEARCH ERROR =====\n{exc}"

            self.result_queue.put(("status", "Gömülü AI çalışıyor…"))
            provider = EmbeddedAIProvider(n_ctx=2048, n_threads=2, max_tokens=256)
            memory = LocalMemory()
            memory.remember(user_input)
            agent = AnneAgent(provider, memory, workspace=str(Path.home() / ".anne" / "workspace"))
            result = agent.run(
                user_input,
                memory_context=memory.load_context(),
                external_context=external_context,
            )
            memory.save_learning(result.learning, response=result.response, confidence=result.confidence)
            self.result_queue.put(("response", result))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def _poll_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "response":
                    result = payload
                    self._append("ANNE", result.response)
                    self.status.configure(text=f"Tamam • confidence {result.confidence:.2f}")
                elif kind == "web":
                    results = payload
                    self._append(
                        "WEB RESEARCH",
                        "\n".join(f"{i}. {item['title']}\n{item['url']}" for i, item in enumerate(results, 1))
                        if results else "Sonuç bulunamadı.",
                    )
                elif kind == "model_progress":
                    received, total = payload
                    received_mb = received / (1024 * 1024)
                    if total > 0:
                        total_mb = total / (1024 * 1024)
                        percent = min(100.0, received * 100.0 / total)
                        self.progress.stop()
                        self.progress.configure(mode="determinate", value=percent)
                        self.progress_label.configure(
                            text=f"{received_mb:.1f} MB / {total_mb:.1f} MB  •  %{percent:.1f}"
                        )
                    else:
                        self.progress.configure(mode="indeterminate")
                        self.progress.start(10)
                        self.progress_label.configure(text=f"{received_mb:.1f} MB indirildi…")
                    self.model_status.configure(text="Model indiriliyor…")
                elif kind == "model":
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=100)
                    self.download_button.configure(state="normal", text="Modeli Yenile")
                    self.refresh_status()
                    self.status.configure(text="Embedded AI modeli hazır.")
                elif kind == "download_error":
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self.refresh_status()
                    self._append("HATA", f"Model indirme başarısız: {payload}")
                    self.status.configure(text="Model indirme başarısız.")
                elif kind == "status":
                    self.status.configure(text=str(payload))
                else:
                    self._append("HATA", str(payload))
                    self.status.configure(text="Hata")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)

    def _append(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{speaker}\n{text}\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")


if __name__ == "__main__":
    EmbeddedAnneTinker().mainloop()
