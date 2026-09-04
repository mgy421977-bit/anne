"""ANNE Native Cognitive Tinker: no Ollama, no embedded LLM, native six-stage cognition."""

from __future__ import annotations

import json
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.agent.local_memory import LocalMemory
from anne.core.ai_kernel import AnneCognitiveEngine, CognitiveState, PHASES
from anne.core.knowledge_transfer import KnowledgeTransferEngine
from anne.tools.web_research import WebResearchClient

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_CONTEXT_CHARS = 12_000


class AnneNativeTinker(tk.Tk):
    """ANNE's independent cognitive loop; an LLM is not required for response generation."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Native Cognitive Engine")
        self.geometry("1280x820")
        self.minsize(1050, 700)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.attachments: list[Path] = []
        self.web_research = tk.BooleanVar(value=False)
        self.learning = tk.BooleanVar(value=True)
        self.engine = AnneCognitiveEngine()
        self.transfer = KnowledgeTransferEngine()
        self._build_ui()
        self.refresh_status()
        self.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.LabelFrame(root, text="ANNE Native Cognitive Engine")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="DUY → BAK → GÖR → ANLA → HİSSET → YAP → ÖĞREN").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(7, 2)
        )
        self.status_label = ttk.Label(header, text="ANNE çekirdeği hazırlanıyor…")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        self.phase_frame = ttk.Frame(header)
        self.phase_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=5)
        self.phase_labels: dict[str, ttk.Label] = {}
        for i, phase in enumerate(PHASES[:6]):
            label = ttk.Label(self.phase_frame, text=f"{phase} ○", width=11, anchor="center")
            label.grid(row=0, column=i, padx=2)
            self.phase_labels[phase] = label
        ttk.Label(header, text="LLM: YOK • Ollama: YOK • Native AI: AKTİF").grid(
            row=0, column=2, rowspan=2, sticky="e", padx=10
        )

        controls = ttk.Frame(header)
        controls.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=(2, 7))
        ttk.Checkbutton(controls, text="İnternet araştırması", variable=self.web_research).pack(side="left")
        ttk.Checkbutton(controls, text="Etkileşimden öğren", variable=self.learning).pack(side="left", padx=20)
        ttk.Button(controls, text="Bilgi Durumu", command=self.show_stats).pack(side="right")
        ttk.Button(controls, text="Öğretmen Bilgisi Aktar", command=self.transfer_dialog).pack(side="right", padx=6)

        files = ttk.LabelFrame(root, text="Araştırma Dosyaları")
        files.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        files.columnconfigure(0, weight=1)
        self.file_list = tk.Listbox(files, height=3, selectmode="extended")
        self.file_list.grid(row=0, column=0, sticky="ew", padx=8, pady=7)
        buttons = ttk.Frame(files)
        buttons.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=7)
        ttk.Button(buttons, text="Dosya Ekle", command=self.add_files).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Seçileni Sil", command=self.remove_selected).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Temizle", command=self.clear_files).pack(fill="x", pady=2)
        ttk.Label(files, text="Dosyalar yalnızca kanıt/bağlam olarak kullanılır; çalıştırılmaz.").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6)
        )

        chat = ttk.LabelFrame(root, text="ANNE")
        chat.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        chat.columnconfigure(0, weight=1)
        chat.rowconfigure(0, weight=1)
        self.output = scrolledtext.ScrolledText(chat, wrap="word", font=("Segoe UI", 10))
        self.output.grid(row=0, column=0, sticky="nsew", padx=7, pady=7)
        self.output.configure(state="disabled")

        inp = ttk.Frame(root)
        inp.grid(row=3, column=0, sticky="ew")
        inp.columnconfigure(0, weight=1)
        self.input_box = tk.Text(inp, height=4, wrap="word", font=("Segoe UI", 10))
        self.input_box.grid(row=0, column=0, sticky="ew")
        self.input_box.bind("<Control-Return>", lambda _e: self.send())
        actions = ttk.Frame(inp)
        actions.grid(row=0, column=1, sticky="ns", padx=(7, 0))
        ttk.Button(actions, text="Gönder", command=self.send).pack(fill="x", pady=(0, 4))
        ttk.Button(actions, text="Temizle", command=lambda: self.input_box.delete("1.0", "end")).pack(fill="x")
        self.footer = ttk.Label(root, text="Hazır", anchor="w")
        self.footer.grid(row=4, column=0, sticky="ew", pady=(4, 0))

    def _append(self, speaker: str, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", f"\n{speaker}\n{text}\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _set_phase(self, active: str) -> None:
        for phase, label in self.phase_labels.items():
            label.configure(text=f"{phase} {'●' if phase == active else '○'}")

    def refresh_status(self) -> None:
        stats = self.transfer.stats()
        self.status_label.configure(
            text=f"Native AI aktif • {stats['packets']} transfer paketi • {stats['facts']} bilgi • LLM gerektirmez"
        )

    def show_stats(self) -> None:
        stats = self.transfer.stats()
        messagebox.showinfo("ANNE Bilgi Durumu", "\n".join(f"{k}: {v}" for k, v in stats.items()))

    def transfer_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("ANNE — Öğretmen Bilgisi Aktar")
        dialog.geometry("820x620")
        dialog.transient(self)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)
        ttk.Label(
            dialog,
            text="Öğretmen modelden çıkarılmış yapılandırılmış bilgi paketlerini ANNE'nin kendi bilgi deposuna aktar. Model ağırlıkları kopyalanmaz.",
            wraplength=780,
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        box = scrolledtext.ScrolledText(dialog, wrap="word", font=("Consolas", 10))
        box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        box.insert("1.0", '{\n  "topic": "ornek",\n  "facts": ["..."],\n  "patterns": ["..."],\n  "rules": ["..."],\n  "examples": ["..."],\n  "cautions": ["..."],\n  "source": "teacher"\n}')
        actions = ttk.Frame(dialog)
        actions.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ttk.Button(actions, text="JSON Dosyası Aç", command=lambda: self.open_json(box)).pack(side="left")
        ttk.Button(actions, text="ANNE'ye Aktar", command=lambda: self.apply_transfer(box, dialog)).pack(side="right")

    def open_json(self, box: tk.Text) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("JSONL", "*.jsonl"), ("All", "*.*")])
        if not path:
            return
        try:
            box.delete("1.0", "end")
            box.insert("1.0", Path(path).read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            messagebox.showerror("ANNE", str(exc))

    def apply_transfer(self, box: tk.Text, dialog: tk.Toplevel) -> None:
        try:
            payload = json.loads(box.get("1.0", "end").strip())
            packets = payload if isinstance(payload, list) else [payload]
            added = self.transfer.ingest(packets)
            self.refresh_status()
            self._append("ANNE ÖĞRENME", f"{added} bilgi paketi ANNE'nin yerel belleğine işlendi.")
            dialog.destroy()
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            messagebox.showerror("Aktarım Hatası", str(exc))

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Araştırma dosyaları", filetypes=[("Text/JSON", "*.txt *.md *.json *.csv *.py *.js *.ts"), ("All", "*.*")])
        for raw in paths:
            path = Path(raw)
            if path not in self.attachments:
                self.attachments.append(path)
                self.file_list.insert("end", str(path))

    def remove_selected(self) -> None:
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
            self.attachments.pop(index)

    def clear_files(self) -> None:
        self.attachments.clear()
        self.file_list.delete(0, "end")

    def _build_context(self) -> str:
        parts: list[str] = []
        remaining = MAX_CONTEXT_CHARS
        for path in self.attachments:
            if path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError(f"{path.name} 4 MB sınırını aşıyor")
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                continue
            chunk = f"===== FILE: {path.name} =====\n{text}"[:remaining]
            parts.append(chunk)
            remaining -= len(chunk)
            if remaining <= 0:
                break
        return "\n\n".join(parts)

    def send(self) -> None:
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            return
        try:
            context = self._build_context()
        except Exception as exc:
            messagebox.showwarning("ANNE", str(exc))
            return
        self.input_box.delete("1.0", "end")
        self._append("YOU", text)
        self.footer.configure(text="ANNE bilişsel döngüyü çalıştırıyor…")
        threading.Thread(target=self._worker, args=(text, context), daemon=True).start()

    @staticmethod
    def _native_response(state: CognitiveState, knowledge: str, web_used: bool) -> str:
        intent = state.task.lower()
        concepts = ", ".join(state.concepts[:8]) or "genel konu"
        best = max(state.hypotheses, key=lambda item: item.score, default=None)
        if any(word in intent for word in ("merhaba", "selam", "hey")):
            return f"Merhaba. Ben ANNE. Girdiyi kendi bilişsel döngümden geçirdim. Algıladığım kavramlar: {concepts}. Şu anda güven düzeyim {state.confidence:.2f}; konuşma ilerledikçe bağlam ve bilgi biriktirebilirim."
        if "kendini" in intent and ("özetle" in intent or "anlat" in intent or "tanıt" in intent):
            return (
                "Ben ANNE — DUY, BAK, GÖR, ANLA, HİSSET ve YAP aşamalarından oluşan, ÖĞREN ile geri beslenen "
                "model-bağımsız bir bilişsel çekirdeğim. Bir dil modeline sahip olmadan da girdiyi ayrıştırabilir, "
                "hipotezler üretebilir, belirsizliği işaretleyebilir ve sonraki adımı seçebilirim. "
                f"Bu döngüde güvenim {state.confidence:.2f}, belirsizliğim {state.uncertainty:.2f}."
            )
        if state.unknown:
            action = state.actions[0] if state.actions else "Ek kanıt topla ve doğrula"
            source_line = "İnternet araştırması kullanıldı." if web_used else "Harici kanıt kullanılmadı."
            return (
                f"Bu girdiyi işledim. Ana kavramlar: {concepts}. {source_line} "
                f"Mevcut durumda kesin bilgi üretmek için yeterli doğrulanmış kanıtım yok. "
                f"HİSSET aşamam güveni {state.confidence:.2f}, belirsizliği {state.uncertainty:.2f} hesapladı. "
                f"Önerdiğim sonraki adım: {action}."
            )
        evidence = f" {len(state.evidence)} kanıt kaydı bulundu."
        hypothesis = best.text if best else "Mevcut bağlamı sürdürmek"
        learning = f" Bu döngüden {len(state.lessons)} ders kaydettim." if state.lessons else ""
        return (
            f"Girdiyi kendi bilişsel motorumla değerlendirdim. Kavramlar: {concepts}.{evidence} "
            f"En güçlü yorumum: {hypothesis}. Güvenim {state.confidence:.2f}; belirsizliğim {state.uncertainty:.2f}. "
            f"Sonraki adım: {state.actions[0] if state.actions else 'Sonucu gözlemle ve kaydet'}.{learning}"
        )

    def _worker(self, text: str, context: str) -> None:
        try:
            memory = LocalMemory()
            self.engine.cycle(text, memory=memory.load_context(), evidence=[context] if context else [])
            state = self.engine.snapshot()
            for phase in PHASES[:6]:
                self.result_queue.put(("phase", phase))
            web_used = False
            if self.web_research.get():
                self.result_queue.put(("status", "Web araştırması yapılıyor…"))
                try:
                    results = WebResearchClient().search(text, max_results=4)
                    web_used = bool(results)
                    if results:
                        context = WebResearchClient.format_results(results) + "\n\n" + context
                        self.result_queue.put(("web", results))
                except Exception as exc:
                    context += f"\n\nWEB ERROR: {exc}"
            knowledge = self.transfer.context()
            response = self._native_response(state, knowledge, web_used)
            if self.learning.get():
                packet = {
                    "topic": state.concepts[0] if state.concepts else "general",
                    "facts": state.known[:4],
                    "patterns": state.observations[-4:],
                    "rules": state.actions[:2],
                    "examples": [text[:500]],
                    "cautions": state.unknown[:3],
                    "source": "ANNE-native-cycle",
                }
                self.transfer.ingest([packet])
                self.engine.ogren(response, "Native cycle completed and stored.")
            self.result_queue.put(("response", response))
            self.result_queue.put(("status", f"ANNE döngüyü tamamladı • güven {state.confidence:.2f} • ÖĞREN güncellendi"))
            self.result_queue.put(("refresh", None))
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
                elif kind == "web":
                    results = payload
                    self._append("WEB RESEARCH", "\n".join(f"{i}. {item['title']}\n{item['url']}" for i, item in enumerate(results, 1)))
                elif kind == "status":
                    self.footer.configure(text=str(payload))
                elif kind == "refresh":
                    self.refresh_status()
                else:
                    self._append("HATA", str(payload))
                    self.footer.configure(text="Hata")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneNativeTinker().mainloop()
