"""ANNE Hybrid Teacher Tinker.

Qwen answers; ANNE owns the cognitive loop, analyzes the response, extracts
reusable response/reasoning patterns, stores them, and feeds them back into
future teacher prompts.
"""

from __future__ import annotations

import queue
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.agent.local_memory import LocalMemory
from anne.core.ai_kernel import AnneCognitiveEngine
from anne.core.data_paths import anne_data_root, ensure_data_dirs
from anne.core.knowledge_transfer import KnowledgeTransferEngine
from anne.core.training_program import LESSONS, current_lesson
from anne.providers.embedded import EmbeddedAIProvider


class HybridTinker(tk.Tk):
    def __init__(self) -> None:
        ensure_data_dirs()
        super().__init__()
        self.title("ANNE AI — Hybrid Teacher / Student")
        self.geometry("1280x820")
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.engine = AnneCognitiveEngine()
        self.transfer = KnowledgeTransferEngine()
        self.memory = LocalMemory()
        self.learning = tk.BooleanVar(value=True)
        self.lesson_index = 0
        self._build()
        self._refresh()
        self.after(100, self._poll)

    def _build(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.LabelFrame(root, text="ANNE HYBRID")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="QWEN ÖĞRETMEN → ANNE ANALİZ → ÖRÜNTÜ ÖĞRENME → SONRAKİ QWEN CEVABI",
        ).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.status = ttk.Label(header, text="Hazır")
        self.status.grid(row=1, column=0, sticky="w", padx=8)
        self.lesson = ttk.Label(header, text="")
        self.lesson.grid(row=2, column=0, sticky="w", padx=8, pady=5)
        ttk.Checkbutton(
            header, text="Qwen cevabından öğren", variable=self.learning
        ).grid(row=3, column=0, sticky="w", padx=8, pady=5)

        info = ttk.LabelFrame(root, text="ANNE Veri Alanı")
        info.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(
            info,
            text=f"Kalıcı veri: {anne_data_root()}    •    Eğitim: {len(LESSONS)} ders",
        ).pack(anchor="w", padx=8, pady=6)

        chat = ttk.LabelFrame(root, text="ANNE")
        chat.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        chat.columnconfigure(0, weight=1)
        chat.rowconfigure(0, weight=1)
        self.output = scrolledtext.ScrolledText(
            chat, wrap="word", font=("Segoe UI", 10)
        )
        self.output.grid(row=0, column=0, sticky="nsew", padx=7, pady=7)
        self.output.configure(state="disabled")

        bottom = ttk.Frame(root)
        bottom.grid(row=3, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self.input_box = tk.Text(bottom, height=4, wrap="word", font=("Segoe UI", 10))
        self.input_box.grid(row=0, column=0, sticky="ew")
        ttk.Button(bottom, text="Gönder", command=self.send).grid(
            row=0, column=1, sticky="ns", padx=(7, 0)
        )

    def _append(self, who: str, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", f"\n{who}\n{text}\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _refresh(self) -> None:
        stats = self.transfer.stats()
        lesson = current_lesson(self.lesson_index)
        self.lesson.configure(
            text=f"DERS {lesson.id}: {lesson.title} — {lesson.practice}"
        )
        self.status.configure(
            text=f"ANNE hazır • {stats['packets']} paket • "
            f"{stats['style_patterns']} cevap örüntüsü • {stats['rules']} kural"
        )

    @staticmethod
    def _analyze_response(response: str) -> dict[str, list[str]]:
        text = response.strip()
        style: list[str] = []
        patterns: list[str] = []
        rules: list[str] = []
        if re.search(r"\n\s*[-•]\s", text):
            style.append("Gerektiğinde madde işaretli yapı kullan")
        if re.search(r"\n\s*\d+[.)]\s", text):
            style.append("Adımları numaralı yapı ile sun")
        if len(text) >= 500:
            style.append("Karmaşık konularda ayrıntılı açıklama yap")
        else:
            style.append("Basit konularda gereksiz uzatmadan cevapla")
        if any(
            word in text.lower()
            for word in ("ancak", "fakat", "öte yandan", "belirsiz", "kesin değil")
        ):
            patterns.append("Alternatif veya belirsizlik durumunu belirt")
        if re.search(r"[:?]\s*\n", text):
            patterns.append("Ana cevabı açıklama veya alt başlıklarla destekle")
        if any(word in text.lower() for word in ("örneğin", "mesela", "örnek")):
            patterns.append("Soyut açıklamayı örnekle somutlaştır")
        if any(word in text.lower() for word in ("kanıt", "kaynak", "veri")):
            rules.append("İddiaları mümkün olduğunda kanıt veya kaynakla ilişkilendir")
        if not rules:
            rules.append("Sonucu gerekçesiyle birlikte ver")
        return {"style": style[:3], "patterns": patterns[:3], "rules": rules[:3]}

    def send(self) -> None:
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            return
        self.input_box.delete("1.0", "end")
        self._append("YOU", text)
        threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text: str) -> None:
        try:
            lesson = current_lesson(self.lesson_index)
            memory_context = self.memory.load_context(6)
            learned = self.transfer.context(limit=12, topic=text)
            state = self.engine.cycle(text, memory=memory_context, knowledge=learned)

            # Keep the teacher prompt compact. The 0.5B model tends to echo
            # long instructions instead of answering when overloaded.
            system = (
                "Sen Qwen adlı öğretmen modelisin. Bir öğrencinin sorusuna doğal, "
                "kısa ve doğru bir cevap örneği ver. Talimatları veya ders metnini "
                "tekrar etme. Kullanıcının istediği şeyi doğrudan cevapla. "
                "Belirsizlik varsa açıkça söyle."
            )
            prompt = (
                f"Ders: {lesson.title}\n"
                f"Hedef: {lesson.objective}\n"
                f"Kısa pratik: {lesson.practice}\n"
                f"ANNE durumu: aşama={state.phase}, güven={state.confidence:.2f}, "
                f"belirsizlik={state.uncertainty:.2f}\n"
            )
            if learned:
                prompt += f"ANNE'nin daha önce öğrendiği ilkeler:\n{learned}\n"
            prompt += (
                "\nÖnemli: Yukarıdaki ders cümlelerini kopyalama. Yeni bir cevap üret.\n"
                f"Kullanıcı: {text}\n"
                "Cevap:"
            )

            provider = EmbeddedAIProvider(
                n_ctx=2048,
                n_threads=2,
                max_tokens=180,
                temperature=0.35,
                repeat_penalty=1.12,
                top_p=0.9,
            )
            self.result_queue.put(("status", "Qwen öğretmen cevaplıyor…"))
            response = provider.ask(prompt, system_instruction=system).strip()
            if not response:
                raise RuntimeError("Qwen boş yanıt verdi")

            analysis = self._analyze_response(response)
            if self.learning.get():
                packet = {
                    "topic": text[:120],
                    "patterns": analysis["patterns"],
                    "rules": analysis["rules"],
                    "response_style": analysis["style"],
                    "examples": [response[:1200]],
                    "source": "Qwen-teacher-analysis",
                }
                self.transfer.ingest([packet])
                self.engine.ogren(
                    response,
                    "Qwen cevabı analiz edildi; cevap örüntüleri ANNE bilgi deposuna kaydedildi.",
                )
                self.memory.remember(text)
                self.memory.save(
                    text,
                    response,
                    "Qwen cevabı ANNE tarafından analiz edildi ve örüntüler çıkarıldı.",
                    state.confidence,
                )
                self.lesson_index = (self.lesson_index + 1) % len(LESSONS)

            self.result_queue.put(("response", response))
            self.result_queue.put(("analysis", analysis))
            self.result_queue.put(("refresh", None))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "response":
                    self._append("QWEN / ÖĞRETMEN", str(payload))
                elif kind == "analysis":
                    data = payload
                    lines = [
                        *("• " + x for x in data["style"]),
                        *("• " + x for x in data["patterns"]),
                        *("• " + x for x in data["rules"]),
                    ]
                    self._append("ANNE ANALİZ", "Öğrendiği cevap örüntüleri:\n" + "\n".join(lines))
                elif kind == "status":
                    self.status.configure(text=str(payload))
                elif kind == "refresh":
                    self._refresh()
                else:
                    self._append("HATA", str(payload))
        except queue.Empty:
            pass
        self.after(100, self._poll)


if __name__ == "__main__":
    HybridTinker().mainloop()
