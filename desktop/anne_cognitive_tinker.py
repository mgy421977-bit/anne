"""ANNE Cognitive Tinker: six-stage native cognitive engine plus optional language model."""

from __future__ import annotations

import json
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
from anne.core.ai_kernel import AnneCognitiveEngine, PHASES
from anne.core.knowledge_transfer import KnowledgeTransferEngine
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


class AnneCognitiveTinker(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Cognitive Engine Tinker")
        self.geometry("1280x820")
        self.minsize(1050, 700)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.attachments: list[Path] = []
        self.web_research = tk.BooleanVar(value=False)
        self.learn_from_cycle = tk.BooleanVar(value=True)
        self.engine = AnneCognitiveEngine()
        self.transfer = KnowledgeTransferEngine()
        self._build_ui()
        self.refresh_status()
        self.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        header = ttk.LabelFrame(root, text="ANNE Cognitive Engine")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="DUY → BAK → GÖR → ANLA → HİSSET → YAP → ÖĞREN").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(7, 3)
        )
        self.engine_status = ttk.Label(header, text="Motor hazırlanıyor…")
        self.engine_status.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=3)
        self.phase_frame = ttk.Frame(header)
        self.phase_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=5)
        self.phase_labels: dict[str, ttk.Label] = {}
        for index, phase in enumerate(PHASES[:6]):
            label = ttk.Label(self.phase_frame, text=f"{phase} ○", width=11, anchor="center")
            label.grid(row=0, column=index, padx=2)
            self.phase_labels[phase] = label
        self.learn_badge = ttk.Label(header, text="Öğrenme: AÇIK")
        self.learn_badge.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)

        controls = ttk.Frame(header)
        controls.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=(2, 7))
        ttk.Checkbutton(controls, text="İnternet araştırması", variable=self.web_research).pack(side="left")
        ttk.Checkbutton(controls, text="Etkileşimden öğren", variable=self.learn_from_cycle).pack(side="left", padx=20)
        ttk.Button(controls, text="Öğretmen Bilgisi Aktar", command=self.open_transfer_dialog).pack(side="right")
        ttk.Button(controls, text="Bilgi Durumu", command=self.show_knowledge_stats).pack(side="right", padx=6)

        research = ttk.LabelFrame(root, text="Araştırma Dosyaları")
        research.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        research.columnconfigure(0, weight=1)
        self.file_list = tk.Listbox(research, height=3, selectmode="extended")
        self.file_list.grid(row=0, column=0, sticky="ew", padx=8, pady=7)
        buttons = ttk.Frame(research)
        buttons.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=7)
        ttk.Button(buttons, text="Dosya Ekle", command=self.add_files).pack(fill="x", pady=(0, 3))
        ttk.Button(buttons, text="Seçileni Sil", command=self.remove_selected_files).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Temizle", command=self.clear_files).pack(fill="x", pady=3)
        ttk.Label(research, text="TXT / MD / kod / JSON / CSV / PDF / DOCX • yalnızca bağlam olarak kullanılır").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6)
        )

        chat_frame = ttk.LabelFrame(root, text="ANNE")
        chat_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        self.chat = scrolledtext.ScrolledText(chat_frame, wrap="word", font=("Segoe UI", 10))
        self.chat.grid(row=0, column=0, sticky="nsew", padx=7, pady=7)
        self.chat.configure(state="disabled")

        input_frame = ttk.Frame(root)
        input_frame.grid(row=4, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        self.input_box = tk.Text(input_frame, height=4, wrap="word", font=("Segoe UI", 10))
        self.input_box.grid(row=0, column=0, sticky="ew")
        self.input_box.bind("<Control-Return>", lambda _event: self.send())
        action = ttk.Frame(input_frame)
        action.grid(row=0, column=1, sticky="ns", padx=(7, 0))
        ttk.Button(action, text="Gönder", command=self.send).pack(fill="x", pady=(0, 4))
        ttk.Button(action, text="Temizle", command=lambda: self.input_box.delete("1.0", "end")).pack(fill="x")
        self.status = ttk.Label(root, text="Hazır", anchor="w")
        self.status.grid(row=5, column=0, sticky="ew", pady=(4, 0))

    def _append(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{speaker}\n{text}\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _set_phase(self, active: str) -> None:
        for phase, label in self.phase_labels.items():
            label.configure(text=f"{phase} {'●' if phase == active else '○'}")

    def refresh_status(self) -> None:
        stats = self.transfer.stats()
        provider = EmbeddedAIProvider()
        model_text = "model hazır" if provider.is_installed() else "model yok"
        self.engine_status.configure(text=f"Native engine • {model_text} • {stats['packets']} transfer paketi • {stats['facts']} bilgi")
        self.learn_badge.configure(text=f"Öğrenme: {'AÇIK' if self.learn_from_cycle.get() else 'KAPALI'}")

    def show_knowledge_stats(self) -> None:
        stats = self.transfer.stats()
        messagebox.showinfo(
            "ANNE Bilgi Durumu",
            "\n".join(f"{key}: {value}" for key, value in stats.items()),
        )

    def open_transfer_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("ANNE — Öğretmen Bilgisi Aktar")
        dialog.geometry("820x620")
        dialog.transient(self)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)
        ttk.Label(
            dialog,
            text="Yapılandırılmış öğretmen bilgisini JSON olarak aktar. Bu işlem model ağırlığı kopyalamaz; bilgi, örnek, kural ve akıl yürütme örüntülerini ANNE'nin yerel bilgi deposuna işler.",
            wraplength=780,
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        box = scrolledtext.ScrolledText(dialog, wrap="word", font=("Consolas", 10))
        box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        box.insert(
            "1.0",
            '{\n  "topic": "ornek",\n  "facts": ["..."],\n  "patterns": ["..."],\n  "rules": ["..."],\n  "examples": ["..."],\n  "cautions": ["..."],\n  "source": "teacher"\n}',
        )
        actions = ttk.Frame(dialog)
        actions.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ttk.Button(actions, text="JSON Dosyası Aç", command=lambda: self.import_transfer_file(box)).pack(side="left")
        ttk.Button(actions, text="ANNE'ye Aktar", command=lambda: self.apply_transfer(box, dialog)).pack(side="right")

    def import_transfer_file(self, box: tk.Text) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("JSONL", "*.jsonl"), ("All files", "*.*")])
        if not path:
            return
        try:
            box.delete("1.0", "end")
            box.insert("1.0", Path(path).read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            messagebox.showerror("ANNE", str(exc))

    def apply_transfer(self, box: tk.Text, dialog: tk.Toplevel) -> None:
        raw = box.get("1.0", "end").strip()
        try:
            payload = json.loads(raw)
            packets = payload if isinstance(payload, list) else [payload]
            added = self.transfer.ingest(packets)
            self.refresh_status()
            self._append("ANNE LEARNING", f"{added} transfer paketi işlendi ve yerel bilgi deposuna eklendi.")
            dialog.destroy()
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            messagebox.showerror("Aktarım Hatası", str(exc))

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Araştırma dosyaları",
            filetypes=[("Research files", "*.txt *.md *.rst *.py *.js *.ts *.json *.yaml *.yml *.toml *.csv *.tsv *.xml *.html *.css *.sql *.pdf *.docx"), ("All files", "*.*")],
        )
        for raw in paths:
            path = Path(raw)
            if path not in self.attachments:
                self.attachments.append(path)
                self.file_list.insert("end", str(path))

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
            messagebox.showwarning("ANNE", str(exc))
            return
        self.input_box.delete("1.0", "end")
        self._append("YOU", user_input)
        self.status.configure(text="ANNE bilişsel döngüyü başlatıyor…")
        threading.Thread(target=self._worker, args=(user_input, external_context), daemon=True).start()

    def _worker(self, user_input: str, external_context: str) -> None:
        try:
            evidence = [external_context] if external_context.strip() else []
            memory = LocalMemory()
            knowledge_context = self.transfer.context()
            state = self.engine.cycle(
                user_input,
                memory=memory.load_context(),
                evidence=evidence,
            )
            for phase in ("DUY", "BAK", "GÖR", "ANLA", "HİSSET", "YAP"):
                self.result_queue.put(("phase", phase))

            if self.web_research.get():
                self.result_queue.put(("status", "Web araştırması yapılıyor…"))
                try:
                    results = WebResearchClient().search(user_input, max_results=4)
                    external_context = WebResearchClient.format_results(results) + "\n\n" + external_context
                    self.result_queue.put(("web", results))
                except Exception as exc:
                    external_context += f"\n\n===== WEB RESEARCH ERROR =====\n{exc}"

            provider = EmbeddedAIProvider(n_ctx=2048, n_threads=2, max_tokens=256)
            self.result_queue.put(("status", "ANNE düşünce durumunu ifade ediyor…"))
            prompt_context = json.dumps(state.__dict__, ensure_ascii=False, default=lambda value: value.__dict__)
            prompt = (
                "ANNE'nin kendi bilişsel motoru tarafından üretilen durumu esas al. "
                "Sen onun yerine düşünme; yalnızca insan tarafından okunabilir bir yanıt üret. "
                "Belirsizlikleri ve kanıt eksiklerini saklama.\n\n"
                f"ANNE COGNITIVE STATE:\n{prompt_context}\n\n"
                f"TRANSFERRED KNOWLEDGE:\n{knowledge_context or '(none)'}\n\n"
                f"EXTERNAL CONTEXT:\n{external_context or '(none)'}\n\n"
                f"USER:\n{user_input}"
            )
            result_text = provider.ask(prompt)
            if not result_text.strip():
                result_text = state.actions[0] if state.actions else state.observations[-1]

            if self.learn_from_cycle.get():
                lesson = state.actions[0] if state.actions else "Cognitive cycle completed"
                packet = {
                    "topic": state.concepts[0] if state.concepts else "general",
                    "patterns": [item for item in state.observations if item.startswith(("GÖR:", "HİSSET:"))][-4:],
                    "rules": state.actions[:2],
                    "examples": [result_text[:600]],
                    "cautions": state.unknown[:3],
                    "source": "ANNE-interaction",
                }
                self.transfer.ingest([packet])
                self.engine.ogren(result_text, lesson)

            self.result_queue.put(("response", result_text))
            self.result_queue.put(("confidence", state.confidence))
            self.result_queue.put(("status", "ANNE döngüyü tamamladı • ÖĞREN güncellendi"))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def _poll_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "phase":
                    self._set_phase(str(payload))
                elif kind == "response":
                    self._append("ANNE", str(payload))
                elif kind == "confidence":
                    self.engine_status.configure(text=f"Bilişsel döngü tamamlandı • güven {float(payload):.2f}")
                    self.refresh_status()
                elif kind == "web":
                    results = payload
                    if results:
                        self._append("WEB RESEARCH", "\n".join(f"{i}. {item['title']}\n{item['url']}" for i, item in enumerate(results, 1)))
                elif kind == "status":
                    self.status.configure(text=str(payload))
                else:
                    self._append("HATA", str(payload))
                    self.status.configure(text="Hata")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneCognitiveTinker().mainloop()
