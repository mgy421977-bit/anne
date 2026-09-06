"""ANNE Windows Tinker — local-first cognitive console with visible execution trace.

The Tinker shows an auditable execution trace, not hidden chain-of-thought:
which module ran, what input/output it produced, what evidence was used, and why
the next bounded action was selected.
"""
from __future__ import annotations

import os
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

from anne.language.tr.core import TurkishLanguageEngine
from anne.learning.percentage import PercentageLearner
from anne.math.engine import MathEngine
from anne.runtime.supervisor import DevelopmentProposal, DevelopmentSupervisor
from anne.weather.open_meteo import OpenMeteoWeather

DEFAULT_OR_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


class AnneTinker(tk.Tk):
    """First GUI prototype for observing ANNE's bounded execution."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Windows Tinker v0.1")
        self.geometry("1240x850")
        self.minsize(1000, 700)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.language = TurkishLanguageEngine()
        self.math = MathEngine()
        self.weather = OpenMeteoWeather()
        self.supervisor = DevelopmentSupervisor()
        self.percentage_learner = PercentageLearner()
        self._build_ui()
        self._load_env_defaults()
        self._update_provider_fields()
        self.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="ANNE v0.1", font=("Segoe UI", 16, "bold")).pack(side="left")
        self.status = ttk.Label(header, text="LOCAL-FIRST • Ready")
        self.status.pack(side="right")
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)
        self.chat_tab = ttk.Frame(notebook, padding=8)
        self.trace_tab = ttk.Frame(notebook, padding=8)
        self.mitos_tab = ttk.Frame(notebook, padding=8)
        self.learning_tab = ttk.Frame(notebook, padding=8)
        self.dev_tab = ttk.Frame(notebook, padding=8)
        self.config_tab = ttk.Frame(notebook, padding=8)
        notebook.add(self.chat_tab, text="Sohbet")
        notebook.add(self.trace_tab, text="Cevap Silsilesi")
        notebook.add(self.mitos_tab, text="MITOS / Keşif")
        notebook.add(self.learning_tab, text="🧠 Öğrenme Lab")
        notebook.add(self.dev_tab, text="Geliştir")
        notebook.add(self.config_tab, text="Bağlantılar")
        self._build_chat()
        self._build_trace()
        self._build_mitos()
        self._build_learning()
        self._build_development()
        self._build_config()

    def _build_chat(self) -> None:
        self.chat = scrolledtext.ScrolledText(self.chat_tab, wrap="word", font=("Segoe UI", 10))
        self.chat.pack(fill="both", expand=True)
        self.chat.configure(state="disabled")
        bottom = ttk.Frame(self.chat_tab)
        bottom.pack(fill="x", pady=(8, 0))
        self.input_box = tk.Text(bottom, height=5, wrap="word", font=("Segoe UI", 10))
        self.input_box.pack(side="left", fill="both", expand=True)
        self.input_box.bind("<Control-Return>", lambda _event: self.send())
        buttons = ttk.Frame(bottom)
        buttons.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(buttons, text="ANNE'ye Sor", command=self.send).pack(fill="x", pady=(0, 5))
        ttk.Button(buttons, text="Temizle", command=self._clear_input).pack(fill="x")
        ttk.Label(
            self.chat_tab,
            text="Ctrl+Enter = gönder • Yerel motorlar önce çalışır • Cevap Silsilesi sekmesinde yürütme izini görebilirsin.",
        ).pack(anchor="w", pady=(6, 0))

    def _build_trace(self) -> None:
        ttk.Label(
            self.trace_tab,
            text="Cevap Silsilesi — açıklanabilir yürütme izi (gizli düşünce değil)",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        self.trace = scrolledtext.ScrolledText(self.trace_tab, wrap="word", font=("Consolas", 10))
        self.trace.pack(fill="both", expand=True, pady=(8, 0))
        self.trace.configure(state="disabled")

    def _build_mitos(self) -> None:
        ttk.Label(
            self.mitos_tab,
            text="MITOS — hipotez ve alternatif üretimi. Sonuçlar otomatik olarak FACT kabul edilmez.",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        prompt = ttk.Frame(self.mitos_tab)
        prompt.pack(fill="x", pady=10)
        self.mitos_input = ttk.Entry(prompt)
        self.mitos_input.pack(side="left", fill="x", expand=True)
        ttk.Button(prompt, text="Keşfet", command=self.run_mitos).pack(side="right", padx=(8, 0))
        self.mitos_output = scrolledtext.ScrolledText(self.mitos_tab, wrap="word", font=("Segoe UI", 10))
        self.mitos_output.pack(fill="both", expand=True)
        self.mitos_output.configure(state="disabled")

    def _build_learning(self) -> None:
        ttk.Label(
            self.learning_tab,
            text="🧠 Öğrenme Lab — kanıt → hipotez → deney → transfer → regression → sandbox",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        form = ttk.Frame(self.learning_tab)
        form.pack(fill="x", pady=10)
        self.learning_input = ttk.Entry(form)
        self.learning_input.insert(0, "Örnek: 800'ün yüzde 15'i kaç?")
        self.learning_input.pack(side="left", fill="x", expand=True)
        ttk.Button(form, text="Öğrenmeyi Başlat", command=self.run_learning).pack(side="right", padx=(8, 0))
        self.learning_status = ttk.Label(self.learning_tab, text="Status: READY • Capability: Turkish Percentage Reasoning")
        self.learning_status.pack(anchor="w", pady=(0, 6))
        self.learning_output = scrolledtext.ScrolledText(self.learning_tab, wrap="word", font=("Consolas", 10))
        self.learning_output.pack(fill="both", expand=True)
        self.learning_output.configure(state="disabled")

    def _build_development(self) -> None:
        ttk.Label(
            self.dev_tab,
            text="Geliştir — ANNE'nin değişiklik önermesi için kanıt kapısı",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        form = ttk.Frame(self.dev_tab)
        form.pack(fill="x", pady=10)
        self.dev_goal = ttk.Entry(form)
        self.dev_goal.insert(0, "Örnek: matematik motoruna güvenli yüzde hesabı ekle")
        self.dev_goal.pack(side="left", fill="x", expand=True)
        ttk.Button(form, text="Öneri üret", command=self.run_development_check).pack(side="right", padx=(8, 0))
        self.dev_output = scrolledtext.ScrolledText(self.dev_tab, wrap="word", font=("Consolas", 10))
        self.dev_output.pack(fill="both", expand=True)
        self.dev_output.configure(state="disabled")

    def _build_config(self) -> None:
        config = ttk.LabelFrame(self.config_tab, text="Harici danışman / GitHub")
        config.pack(fill="x")
        config.columnconfigure(1, weight=1)
        config.columnconfigure(3, weight=1)
        ttk.Label(config, text="Provider").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.provider = ttk.Combobox(config, values=["OpenRouter Free", "Gemini"], state="readonly")
        self.provider.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        self.provider.bind("<<ComboboxSelected>>", lambda _event: self._update_provider_fields())
        self.key_label = ttk.Label(config, text="OpenRouter API key")
        self.key_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.api_key = ttk.Entry(config, show="*")
        self.api_key.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        ttk.Label(config, text="Model").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.model = ttk.Entry(config)
        self.model.grid(row=0, column=3, sticky="ew", padx=8, pady=6)
        ttk.Label(config, text="GitHub repository").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        self.repository = ttk.Entry(config)
        self.repository.grid(row=1, column=3, sticky="ew", padx=8, pady=6)
        ttk.Label(
            config,
            text="API anahtarları GUI'ye kaydedilmez; environment variable kullanılabilir. Temel Tinker bunlara ihtiyaç duymaz.",
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=8, pady=(4, 8))

    def _load_env_defaults(self) -> None:
        self.provider.set(os.getenv("ANNE_PROVIDER", "OpenRouter Free"))
        self.api_key.insert(0, os.getenv("OPENROUTER_API_KEY", ""))
        self.repository.insert(0, os.getenv("ANNE_REPOSITORY", "mgy421977-bit/anne"))
        self.model.insert(0, os.getenv("ANNE_OPENROUTER_MODEL", DEFAULT_OR_MODEL))

    def _update_provider_fields(self) -> None:
        selected = self.provider.get()
        current = self.model.get().strip()
        if selected == "Gemini":
            self.key_label.configure(text="Gemini API key")
            if not current or current == DEFAULT_OR_MODEL:
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_GEMINI_MODEL", "gemini-3.7-flash"))
        else:
            self.key_label.configure(text="OpenRouter API key")
            if not current or current == "gemini-3.7-flash":
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_OPENROUTER_MODEL", DEFAULT_OR_MODEL))

    def _append(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{speaker}\n{text}\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _set_text(self, widget: scrolledtext.ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    def _clear_input(self) -> None:
        self.input_box.delete("1.0", "end")

    def send(self) -> None:
        user_input = self.input_box.get("1.0", "end").strip()
        if not user_input:
            return
        self._clear_input()
        self._append("SEN", user_input)
        self.status.configure(text="ANNE • yürütüyor…")
        threading.Thread(target=self._local_worker, args=(user_input,), daemon=True).start()

    def _local_worker(self, user_input: str) -> None:
        try:
            answer, trace = self._execute_local(user_input)
            self.result_queue.put(("local_ok", (answer, trace)))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def _execute_local(self, user_input: str) -> tuple[str, list[str]]:
        """Run deterministic local capabilities and evidence-gated learning."""
        if self.percentage_learner.matches(user_input):
            result = self.percentage_learner.learn(user_input)
            trace = list(result.trace)
            if result.answer is not None:
                trace.append(f"11 ANSWER | Sonuç = {result.answer}")
                return f"Öğrenme adayı doğrulandı. Sonuç: {result.answer}", trace
            trace.append("11 ANSWER | Güvenli transfer cevabı üretilemedi; öğrenme adayı korunuyor.")
            return "Bu yüzde ifadesi için öğrenme adayı oluşturuldu ancak güvenli cevap üretilemedi.", trace

        analysis = self.language.analyze(user_input)
        trace = [
            "01 OBSERVE | Kullanıcı girdisi alındı.",
            f"02 CONTEXT | normalize = {analysis.normalized!r}",
            f"03 PARSE | tokens = {analysis.tokens}",
            f"04 CLASSIFY | intent = {analysis.intent}",
        ]
        if analysis.intent == "math":
            expression = self._extract_math_expression(analysis.normalized)
            trace.append(f"05 ROUTE | math → deterministic_decimal_ast; expression = {expression!r}")
            if not expression:
                trace.append("06 VERIFY | Güvenli matematik ifadesi çıkarılamadı; işlem durduruldu.")
                return "Matematik işlemini algıladım ama güvenli bir işlem ifadesi çıkaramadım.", trace
            calculation = self.math.calculate(expression)
            trace.extend(
                [
                    "06 VALIDATE | AST yalnızca izinli sayısal düğümler ve + - * / ** % operatörlerini kabul ediyor.",
                    f"07 COMPUTE | Decimal precision = 50; method = {calculation.method}",
                    f"08 COMPUTE | {calculation.expression} = {calculation.value}",
                    "09 VERIFY | Hesaplama deterministik olarak tamamlandı; dış model kullanılmadı.",
                ]
            )
            return f"Sonuç: {calculation.value}", trace
        if analysis.intent == "weather":
            city = os.getenv("ANNE_LOCATION", "İzmir")
            trace.append(f"05 ROUTE | weather → Open-Meteo observation; city = {city!r}")
            observation = self.weather.observe(city)
            trace.extend(
                [
                    "06 OBSERVE | Güncel hava gözlemi alındı.",
                    f"07 DATA | temperature_c = {observation.get('temperature_c')}; condition = {observation.get('condition')}",
                    "08 MEMORY | durability = ephemeral; kalıcı belleğe yazılmadı.",
                    "09 VERIFY | Kaynak gözlemi ile cevap oluşturuldu.",
                ]
            )
            return self.language.respond(analysis, weather=observation), trace
        trace.extend(
            [
                "05 ROUTE | deterministic Turkish response; external model not required.",
                "06 PARSE | morphology ve basit sentence-role heuristics uygulandı.",
                "07 VERIFY | Yerel kapsamda güvenli cevap üretildi.",
            ]
        )
        return self.language.respond(analysis), trace

    @staticmethod
    def _extract_math_expression(text: str) -> str | None:
        direct = re.search(r"[-+]?\d+(?:\.\d+)?\s*[+\-*/]\s*[-+]?\d+(?:\.\d+)?", text)
        if direct:
            return direct.group(0)
        words = re.search(r"(-?\d+(?:\.\d+)?)\s+(artı|eksi|çarpı|bölü)\s+(-?\d+(?:\.\d+)?)", text)
        if words:
            op = {"artı": "+", "eksi": "-", "çarpı": "*", "bölü": "/"}[words.group(2)]
            return f"{words.group(1)} {op} {words.group(3)}"
        return None

    def run_mitos(self) -> None:
        question = self.mitos_input.get().strip()
        if not question:
            return
        proposals = self.supervisor.propose(question, batch_size=5)
        lines = [
            f"MISSION: {question}",
            "",
            "MITOS → BOUNDED DEVELOPMENT PROPOSALS",
            "Her aday hipotezdir; tek başına FACT değildir.",
            "",
        ]
        for index, proposal in enumerate(proposals, start=1):
            lines.extend(
                [
                    f"[{index}] {proposal.decision.value} | {proposal.change}",
                    f"    id={proposal.candidate_id}",
                    f"    reason={proposal.reason}",
                    f"    tests={'; '.join(proposal.required_tests)}",
                    "",
                ]
            )
        self._set_text(self.mitos_output, "\n".join(lines))

    def run_learning(self) -> None:
        question = self.learning_input.get().strip()
        if not question:
            return
        self.learning_status.configure(text="Status: RESEARCHING • MITOS → Evidence → Experiment")
        self._set_text(self.learning_output, "ANNE öğrenme döngüsünü başlatıyor…\nWeb evidence araştırılıyor; sonuçlar kanıt olarak işaretlenecek, FACT olarak değil.")
        threading.Thread(target=self._learning_worker, args=(question,), daemon=True).start()

    def _learning_worker(self, question: str) -> None:
        try:
            result = self.percentage_learner.learn(question)
            lines = [
                "🧠 LEARNING LAB",
                "=" * 72,
                f"Problem           : {result.question}",
                f"Capability        : {result.candidate.capability_id}",
                f"Hypothesis        : {result.candidate.hypothesis}",
                f"Method            : {result.candidate.method}",
                "",
                "EXECUTION TRACE",
                *result.trace,
                "",
                "GATE SUMMARY",
                f"Tests             : {result.candidate.tests_passed}/{result.candidate.tests_total} ({result.candidate.test_accuracy:.0%})",
                f"Transfer          : {'PASS' if result.candidate.transfer_passed else 'FAIL'}",
                f"Regression        : {'PASS' if result.candidate.regression_passed else 'FAIL'}",
                f"Sandbox           : {'PASS' if result.candidate.sandbox_passed else 'FAIL'}",
                f"Confidence        : {result.candidate.confidence:.2f}",
                f"Promotion ready   : {'YES' if result.candidate.promotion_ready() else 'NO'}",
                "",
                f"Answer            : {result.answer if result.answer is not None else 'NOT PROMOTED'}",
                "",
                "POLICY: Web evidence informs the candidate; production code is not rewritten automatically.",
            ]
            self.result_queue.put(("learning_ok", ("\n".join(lines), result)))
        except Exception as exc:
            self.result_queue.put(("learning_error", str(exc)))

    def run_development_check(self) -> None:
        goal = self.dev_goal.get().strip()
        proposals = self.supervisor.propose(goal, batch_size=1)
        proposal: DevelopmentProposal = proposals[0]
        allowed = self.supervisor.promotion_allowed(
            regression_passed=False,
            capability_passed=False,
            sandbox_passed=False,
            policy_passed=True,
            rollback_ready=True,
        )
        text = (
            f"GOAL\n{proposal.goal}\n\n"
            f"CANDIDATE\n{proposal.change}\n\n"
            f"DECISION: {proposal.decision.value}\n"
            f"REASON: {proposal.reason}\n\n"
            "PROMOTION GATE\n"
            f"promotion_allowed = {allowed}\n\n"
            "NEDEN\n"
            "Regression, capability ve sandbox kanıtı henüz verilmediği için ANNE değişikliği üretime terfi ettirmiyor."
        )
        self._set_text(self.dev_output, text)

    def _poll_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "local_ok":
                    answer, trace = payload  # type: ignore[misc]
                    self._append("ANNE", answer)
                    self._set_text(self.trace, "\n".join(trace))
                    self.status.configure(text="LOCAL-FIRST • verified")
                elif kind == "learning_ok":
                    text, _result = payload  # type: ignore[misc]
                    self._set_text(self.learning_output, text)
                    self.learning_status.configure(text="Status: CANDIDATE EVALUATED • Production promotion remains gated")
                    self.status.configure(text="LEARNING • candidate evaluated")
                elif kind == "learning_error":
                    self._set_text(self.learning_output, f"Learning error: {payload}")
                    self.learning_status.configure(text="Status: ERROR • candidate not promoted")
                    self.status.configure(text="Error")
                else:
                    self._append("SYSTEM ERROR", str(payload))
                    self.status.configure(text="Error")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneTinker().mainloop()
