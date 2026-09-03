"""ANNE Windows Tinker — desktop client with Gemini/OpenRouter and tools."""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.agent.github_memory import GitHubMemory
from anne.agent.runtime import AnneAgent
from anne.providers.gemini import GeminiProvider
from anne.providers.openrouter import OpenRouterProvider


class AnneTinker(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Windows Tinker")
        self.geometry("1120x800")
        self.minsize(900, 650)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.after(100, self._poll_results)
        self._load_env_defaults()
        self._update_provider_fields()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        config = ttk.LabelFrame(root, text="Connection")
        config.pack(fill="x", pady=(0, 10))
        config.columnconfigure(1, weight=1)
        config.columnconfigure(3, weight=1)

        ttk.Label(config, text="Provider").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.provider = ttk.Combobox(config, values=["OpenRouter Free", "Gemini"], state="readonly", width=20)
        self.provider.grid(row=0, column=1, sticky="w", padx=8, pady=6)
        self.provider.bind("<<ComboboxSelected>>", lambda _event: self._update_provider_fields())

        self.key_label = ttk.Label(config, text="OpenRouter API key")
        self.key_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.api_key = ttk.Entry(config, show="*", width=62)
        self.api_key.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="GitHub token").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.github_token = ttk.Entry(config, show="*", width=62)
        self.github_token.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Repository").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.repository = ttk.Entry(config, width=28)
        self.repository.grid(row=0, column=3, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Model").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        self.model = ttk.Entry(config, width=28)
        self.model.grid(row=1, column=3, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Mode").grid(row=2, column=2, sticky="w", padx=8, pady=6)
        self.mode = ttk.Label(config, text="Tool Agent + GitHub Memory")
        self.mode.grid(row=2, column=3, sticky="w", padx=8, pady=6)

        self.status = ttk.Label(config, text="Ready", anchor="w")
        self.status.grid(row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(2, 8))

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

        hint = ttk.Label(
            root,
            text="Ctrl+Enter = Send | ANNE can read GitHub/local files and write durable learning to GitHub memory.",
        )
        hint.pack(anchor="w", pady=(5, 0))

    def _load_env_defaults(self) -> None:
        self.provider.set(os.getenv("ANNE_PROVIDER", "OpenRouter Free"))
        self.api_key.insert(0, os.getenv("OPENROUTER_API_KEY", ""))
        self.github_token.insert(0, os.getenv("GITHUB_TOKEN", ""))
        self.repository.insert(0, os.getenv("ANNE_REPOSITORY", "mgy421977-bit/anne"))
        self.model.insert(0, os.getenv("ANNE_OPENROUTER_MODEL", "openrouter/free"))

    def _update_provider_fields(self) -> None:
        selected = self.provider.get()
        if selected == "Gemini":
            self.key_label.configure(text="Gemini API key")
            if not self.model.get().strip() or self.model.get().strip() == "openrouter/free":
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_GEMINI_MODEL", "gemini-3.7-flash"))
        else:
            self.key_label.configure(text="OpenRouter API key")
            if not self.model.get().strip() or self.model.get().strip() == "gemini-3.7-flash":
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_OPENROUTER_MODEL", "openrouter/free"))

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
        api_key = self.api_key.get().strip()
        github_token = self.github_token.get().strip()
        repository = self.repository.get().strip()
        model = self.model.get().strip()
        if not api_key:
            messagebox.showwarning("Missing API key", f"Enter the {self.provider.get()} API key.")
            return
        if not github_token:
            messagebox.showwarning("Missing token", "Enter a GitHub token with Contents read/write permission.")
            return
        self._clear_input()
        self._append("YOU", user_input)
        self.status.configure(text="ANNE is thinking and can use tools…")
        threading.Thread(
            target=self._worker,
            args=(user_input, api_key, github_token, repository, model, self.provider.get()),
            daemon=True,
        ).start()

    def _worker(
        self,
        user_input: str,
        api_key: str,
        github_token: str,
        repository: str,
        model: str,
        provider_name: str,
    ) -> None:
        try:
            if provider_name == "Gemini":
                provider = GeminiProvider(api_key=api_key, model=model)
            else:
                provider = OpenRouterProvider(api_key=api_key, model=model)
            memory = GitHubMemory(token=github_token, repository=repository)
            agent = AnneAgent(provider, memory, workspace=ROOT)
            result = agent.run(user_input)
            self.result_queue.put(("ok", result))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def _poll_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "ok":
                    result = payload
                    tools = ", ".join(result.tools_used) if result.tools_used else "none"
                    self._append(
                        "ANNE",
                        f"{result.response}\n\n"
                        f"[Tools: {tools}]\n"
                        f"[Learning saved: {result.memory_path} | confidence={result.confidence:.2f}]",
                    )
                    self.status.configure(text="Ready — response and memory completed.")
                else:
                    self._append("SYSTEM ERROR", str(payload))
                    self.status.configure(text="Error — check keys, network, permissions, or provider quota.")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneTinker().mainloop()
