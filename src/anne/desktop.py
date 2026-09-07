"""Minimal Tkinter desktop interface for the ANNE cognitive runtime.

The desktop layer is intentionally thin: it presents the existing guarded
DecisionLoop and does not add new cognitive, safety, or agency authority.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Any

from anne.core.decision_loop import DecisionLoop


APP_TITLE = "ANNE AI — Adaptive Neural Nexus Engine"
STAGES = (
    "FAIL_FAST",
    "DUY",
    "BAK",
    "GÖR",
    "MITOS",
    "SELECT",
    "ANLA",
    "HİSSET",
    "YAP",
)


class AnneDesktop(tk.Tk):
    """Small desktop shell around the existing ANNE cognitive runtime."""

    def __init__(self, loop: DecisionLoop | None = None) -> None:
        super().__init__()
        self.loop = loop
        self.title(APP_TITLE)
        self.geometry("900x720")
        self.minsize(760, 600)
        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x")
        ttk.Label(header, text="ANNE AI", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text="Adaptive Neural Nexus Engine · Minimal Universal Runtime",
        ).pack(anchor="w", pady=(2, 10))

        status = ttk.Frame(root)
        status.pack(fill="x", pady=(0, 12))
        ttk.Label(status, text="RUNTIME: CLASSICAL / MINIMAL").pack(side="left")
        self.status_var = tk.StringVar(value="READY")
        ttk.Label(status, textvariable=self.status_var).pack(side="right")

        ttk.Label(root, text="Input").pack(anchor="w")
        self.input_text = tk.Text(root, height=6, wrap="word", font=("Segoe UI", 11))
        self.input_text.pack(fill="x", pady=(4, 10))
        self.input_text.insert(
            "1.0",
            "Merhaba ANNE. Kendini güvenli ve sınırlı bir bilişsel çevrim içinde test et.",
        )

        self.run_button = ttk.Button(root, text="RUN COGNITIVE CYCLE", command=self._start_cycle)
        self.run_button.pack(anchor="e", pady=(0, 14))

        ttk.Label(root, text="Cognitive Trace").pack(anchor="w")
        trace_frame = ttk.Frame(root)
        trace_frame.pack(fill="x", pady=(4, 12))
        self.stage_vars: dict[str, tk.StringVar] = {}
        for stage in STAGES:
            var = tk.StringVar(value=f"○ {stage}")
            self.stage_vars[stage] = var
            ttk.Label(trace_frame, textvariable=var, width=13).pack(side="left", padx=2)

        ttk.Label(root, text="Result").pack(anchor="w")
        self.result_text = tk.Text(
            root,
            height=14,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.result_text.pack(fill="both", expand=True)

    def _start_cycle(self) -> None:
        raw_input = self.input_text.get("1.0", "end-1c").strip()
        if not raw_input:
            self._show_result("Please enter an input.")
            return

        self.run_button.configure(state="disabled")
        self.status_var.set("RUNNING")
        for stage in STAGES:
            self.stage_vars[stage].set(f"○ {stage}")

        threading.Thread(target=self._run_cycle, args=(raw_input,), daemon=True).start()

    def _run_cycle(self, raw_input: str) -> None:
        try:
            loop = self.loop or DecisionLoop()
            result = loop.run_cognitive(raw_input)
            self.after(0, self._render_result, result)
        except Exception as exc:  # noqa: BLE001 - surface runtime failures in the UI
            self.after(0, self._render_error, exc)

    def _render_result(self, result: Any) -> None:
        trace = getattr(result, "stage_trace", ())
        for stage in STAGES:
            marker = "✓" if stage in trace else "○"
            self.stage_vars[stage].set(f"{marker} {stage}")

        state = getattr(result, "state", None)
        output = getattr(state, "output", {}) or {}
        selection = getattr(result, "selection", None)
        ethic_score = getattr(state, "ethic_score", None)
        context_map = getattr(state, "context_map", {}) or {}
        lines = [
            f"STATUS      : {getattr(result, 'status', 'UNKNOWN')}",
            f"REASON      : {getattr(result, 'reason', '') or '—'}",
            f"VERDICT     : {output.get('verdict', '—')}",
            f"ACTION      : {output.get('action', '—')}",
            f"SOURCE      : {output.get('source', '—')}",
            f"CONFIDENCE  : {output.get('confidence', '—')}",
        ]
        if selection is not None:
            lines.extend(
                [
                    f"SELECTED    : {getattr(selection, 'accepted', '—')}",
                    f"SCORE       : {getattr(selection, 'score', '—')}",
                ]
            )
        lines.extend(
            [
                f"ANLA SCORE  : {context_map.get('anla_score', '—')}",
                f"ETHIC SCORE : {getattr(ethic_score, 'total', '—')}",
                f"HYPOTHESIS  : {output.get('hypothesis', '—')}",
                f"MEMORY      : anne.db",
            ]
        )
        self._show_result("\n".join(lines))
        self.status_var.set(str(getattr(result, "status", "DONE")))
        self.run_button.configure(state="normal")

    def _render_error(self, exc: Exception) -> None:
        self._show_result(f"RUNTIME ERROR\n\n{type(exc).__name__}: {exc}")
        self.status_var.set("ERROR")
        self.run_button.configure(state="normal")

    def _show_result(self, text: str) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")


def main() -> None:
    """Launch the ANNE desktop shell."""
    app = AnneDesktop()
    app.mainloop()


if __name__ == "__main__":
    main()
