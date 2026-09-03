"""ANNE Windows Tinker — a small Tkinter desktop client.

Run from the repository root after installing dependencies:
    python desktop/anne_tinker.py

API keys can be entered in the UI or supplied through environment variables:
    GEMINI_API_KEY
    GITHUB_TOKEN
    ANNE_REPOSITORY (default: mgy421977-bit/anne)
    ANNE_GEMINI_MODEL (default: gemini-3.7-flash)
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.agent.github_memory import GitHubMemory
from anne.agent.runtime import AnneAgent
from anne.providers.gemini import GeminiProvider


class AnneTinker(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Windows Tinker")
        self.geometry("1050x760")
        self.minsize(860, 620)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.after(100, self._poll_results)
        self._load_env_defaults()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        config = ttk.LabelFrame(root, text="Connection")
        config.pack(fill="x", pady=(0, 10))

        ttk.Label(config, text="Gemini API key").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.gemini_key = ttk.Entry(config, show="*", width=62)
        self.gemini_key.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="GitHub token").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.github_token = ttk.Entry(config, show="*", width=62)
        self.github_token.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Repository").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.repository = ttk.Entry(config, width=28)
        self.repository.grid(row=0, column=3, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Model").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        self.model = ttk.Entry(config, width=28)
        self.model.grid(row=1, column=3, sticky="ew", padx=8, pady=6)
        config.columnconfigure(1, weight=1)
        config.columnconfigure(3, weight=1)

        self.status = ttk.Label(config, text="Ready", anchor="w")
        self.status.grid(row=2, column=0, columnspan=4, sticky="ew", padx=8, pady=(2, 8))

        chat_frame = ttk.LabelFrame(root, text="ANNE")
        chat_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.chat = scrolledtext.ScrolledText(chat_frame, wrap="word", font=("Segoe UI", 10))
        self.chat.pack(fill="both", expand=True, padx=8, pady=8)
        self.chat.configure(state="disabled")

        input_frame = ttk.Frame(root)
        input_frame.pack(fill="x")
        self.input_box = tk.Text(input_frame, height=5, wrap="word", font=("Segoe UI", 10))
        self.input_box.pack(side="left", fill="both", expand=True)
        self.input_box.bind("<Control-Return>", lambda _event: self.send())

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(button_frame, text="Send", command=self.send).pack(fill="x", pady=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self._clear_input).pack(fill="x")

        hint = ttk.Label(root, text="Ctrl+Enter = Send  |  Memory is written to GitHub after each successful reply.")
        hint.pack(anchor="w", pady=(5, 0))

    def _load_env_defaults(self) -> None:
        self.gemini_key.insert(0, os.getenv("GEMINI_API_KEY", ""))
        self.github_token.insert(0, os.getenv("GITHUB_TOKEN", ""))
        self.repository.insert(0, os.getenv("ANNE_REPOSITORY", "mgy421977-bit/anne"))
        self.model.insert(0, os.getenv("ANNE_GEMINI_MODEL", "gemini-3.7-flash"))

    def _append(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{speaker}\n{text}\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _clear_input(self) -> None:
        self.input_box.delete("1.0", "end")

    def send(self) -> None:
        user_input = self.input_box.get("1.0", "end").strip()
        if not user_input:
            return
        gemini_key = self.gemini_key.get().strip()
        github_token = self.github_token.get().strip()
        repository = self.repository.get().strip()
        model = self.model.get().strip() or "gemini-3.7-flash"
        if not gemini_key:
            messagebox.showwarning("Missing key", "Enter the Gemini API key.")
            return
        if not github_token:
            messagebox.showwarning("Missing token", "Enter a GitHub token with permission to write to the repository.")
            return
        self._clear_input()
        self._append("YOU", user_input)
        self.status.configure(text="ANNE is thinking…")
        threading.Thread(
            target=self._worker,
            args=(user_input, gemini_key, github_token, repository, model),
            daemon=True,
        ).start()

    def _worker(self, user_input: str, gemini_key: str, github_token: str, repository: str, model: str) -> None:
        try:
            provider = GeminiProvider(api_key=gemini_key, model=model)
            memory = GitHubMemory(token=github_token, repository=repository)
            agent = AnneAgent(provider, memory)
            result = agent.run(user_input)
            self.result_queue.put(("ok", result))
        except Exception as exc:  # UI boundary: surface a concise error.
            self.result_queue.put(("error", str(exc)))

    def _poll_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "ok":
                    result = payload
                    self._append(
                        "ANNE",
                        f"{result.response}\n\n[Learning saved: {result.memory_path} | confidence={result.confidence:.2f}]",
                    )
                    self.status.configure(text="Ready — memory committed to GitHub.")
                else:
                    self._append("SYSTEM ERROR", str(payload))
                    self.status.configure(text="Error — check the keys, network, and GitHub permissions.")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneTinker().mainloop()
