"""ANNE Windows Tinker — pipeline-first desktop client with optional Gemini synthesis."""

from __future__ import annotations

import json
import os
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

from anne import run_pipeline
from anne.agent.github_memory import GitHubMemory
from anne.agent.runtime import AnneAgent
from anne.providers.gemini import GeminiProvider
from anne.providers.openrouter import OpenRouterProvider

DEFAULT_GEMINI_MODEL = "gemini-3.7-flash"
DEFAULT_OR_MODEL = "openrouter/free"
MAX_FILE_BYTES = 4 * 1024 * 1024
TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".py", ".json", ".csv", ".tsv", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".xml", ".html", ".htm", ".sql", ".log"
}


class AnneTinker(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Windows Tinker")
        self.geometry("1180x860")
        self.minsize(980, 700)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.attachments: list[tuple[str, str]] = []
        self._build_ui()
        self._load_env_defaults()
        self._update_provider_fields()
        self.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        config = ttk.LabelFrame(root, text="ANNE Configuration")
        config.pack(fill="x", pady=(0, 10))
        for col in (1, 3):
            config.columnconfigure(col, weight=1)

        ttk.Label(config, text="Mode").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.mode_selector = ttk.Combobox(
            config, values=["Pipeline First", "Agent / Tools"], state="readonly", width=20
        )
        self.mode_selector.grid(row=0, column=1, sticky="w", padx=8, pady=6)
        self.mode_selector.bind("<<ComboboxSelected>>", lambda _e: self._update_mode())

        ttk.Label(config, text="Provider").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.provider = ttk.Combobox(
            config,
            values=["Gemini", "OpenRouter"],
            state="readonly",
            width=20,
        )
        self.provider.grid(row=0, column=3, sticky="w", padx=8, pady=6)
        self.provider.bind("<<ComboboxSelected>>", lambda _e: self._update_provider_fields())

        self.key_label = ttk.Label(config, text="Gemini API key")
        self.key_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.api_key = ttk.Entry(config, show="*", width=62)
        self.api_key.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Model").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        self.model = ttk.Entry(config, width=34)
        self.model.grid(row=1, column=3, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="GitHub token").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.github_token = ttk.Entry(config, show="*", width=62)
        self.github_token.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Repository").grid(row=2, column=2, sticky="w", padx=8, pady=6)
        self.repository = ttk.Entry(config, width=34)
        self.repository.grid(row=2, column=3, sticky="ew", padx=8, pady=6)

        self.synthesis = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            config,
            text="Optional Gemini synthesis after local pipeline",
            variable=self.synthesis,
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        self.mode_status = ttk.Label(config, text="Pipeline First — LLM optional")
        self.mode_status.grid(row=3, column=2, columnspan=2, sticky="w", padx=8, pady=4)

        self.status = ttk.Label(config, text="Ready", anchor="w")
        self.status.grid(row=4, column=0, columnspan=4, sticky="ew", padx=8, pady=(2, 8))

        attach = ttk.LabelFrame(root, text="Research Files")
        attach.pack(fill="x", pady=(0, 10))
        self.attachment_list = tk.Listbox(attach, height=4)
        self.attachment_list.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        attach_buttons = ttk.Frame(attach)
        attach_buttons.pack(side="right", fill="y", padx=(0, 8), pady=8)
        ttk.Button(attach_buttons, text="Add files…", command=self._add_files).pack(fill="x", pady=(0, 5))
        ttk.Button(attach_buttons, text="Remove", command=self._remove_file).pack(fill="x")

        chat_frame = ttk.LabelFrame(root, text="ANNE")
        chat_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.chat = scrolledtext.ScrolledText(chat_frame, wrap="word", font=("Segoe UI", 10))
        self.chat.pack(fill="both", expand=True, padx=8, pady=8)
        self.chat.configure(state="disabled")

        input_frame = ttk.Frame(root)
        input_frame.pack(fill="x")
        self.input_box = tk.Text(input_frame, height=6, wrap="word", font=("Segoe UI", 10))
        self.input_box.pack(side="left", fill="both", expand=True)
        self.input_box.bind("<Control-Return>", lambda _event: self.send())
        buttons = ttk.Frame(input_frame)
        buttons.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(buttons, text="Send", command=self.send).pack(fill="x", pady=(0, 5))
        ttk.Button(buttons, text="Clear", command=self._clear_input).pack(fill="x")

        ttk.Label(
            root,
            text="Ctrl+Enter = Send | Attach Athena/ATHENA notes, PDFs, DOCX, code or text and ANNE will analyze the supplied evidence.",
        ).pack(anchor="w", pady=(5, 0))

    def _load_env_defaults(self) -> None:
        self.mode_selector.set(os.getenv("ANNE_MODE", "Pipeline First"))
        self.provider.set(os.getenv("ANNE_PROVIDER", "Gemini"))
        self.api_key.insert(0, os.getenv("GEMINI_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", ""))
        self.github_token.insert(0, os.getenv("GITHUB_TOKEN", ""))
        self.repository.insert(0, os.getenv("ANNE_REPOSITORY", "mgy421977-bit/anne"))
        self.model.insert(0, os.getenv("ANNE_GEMINI_MODEL", DEFAULT_GEMINI_MODEL))

    def _update_provider_fields(self) -> None:
        provider = self.provider.get()
        current = self.model.get().strip()
        if provider == "Gemini":
            self.key_label.configure(text="Gemini API key")
            if not current or current == DEFAULT_OR_MODEL:
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_GEMINI_MODEL", DEFAULT_GEMINI_MODEL))
        else:
            self.key_label.configure(text="OpenRouter API key")
            if not current or current == DEFAULT_GEMINI_MODEL:
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_OPENROUTER_MODEL", DEFAULT_OR_MODEL))

    def _update_mode(self) -> None:
        self.mode_status.configure(
            text=(
                "Pipeline First — LLM optional"
                if self.mode_selector.get() == "Pipeline First"
                else "Agent / Tools — LLM required"
            )
        )

    def _append(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{speaker}\n{text}\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _clear_input(self) -> None:
        self.input_box.delete("1.0", "end")

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Attach research files",
            filetypes=[
                ("Research/Text", "*.txt *.md *.markdown *.json *.csv *.tsv *.py *.yaml *.yml *.toml *.xml *.html *.htm *.sql *.log"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("All supported", "*.txt *.md *.markdown *.json *.csv *.tsv *.py *.yaml *.yml *.toml *.xml *.html *.htm *.sql *.log *.pdf *.docx"),
            ],
        )
        for raw_path in paths:
            try:
                name, text = self._read_attachment(Path(raw_path))
                if any(existing_name == name for existing_name, _ in self.attachments):
                    continue
                self.attachments.append((name, text))
                self.attachment_list.insert("end", name)
            except Exception as exc:
                messagebox.showerror("Attachment error", f"{Path(raw_path).name}\n\n{exc}")

    def _remove_file(self) -> None:
        selection = list(self.attachment_list.curselection())
        for index in reversed(selection):
            self.attachment_list.delete(index)
            self.attachments.pop(index)

    @staticmethod
    def _read_attachment(path: Path) -> tuple[str, str]:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("File is larger than 4 MB. Please attach a smaller excerpt.")
        ext = path.suffix.casefold()
        if ext in TEXT_EXTENSIONS:
            return path.name, path.read_text(encoding="utf-8", errors="replace")
        if ext == ".docx":
            parts: list[str] = []
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml")
            root = ElementTree.fromstring(xml)
            for node in root.iter():
                if node.tag.endswith("}t") and node.text:
                    parts.append(node.text)
            return path.name, " ".join(parts)
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise ValueError("PDF reading requires pypdf. Install: pip install pypdf") from exc
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return path.name, "\n\n".join(pages)
        raise ValueError(f"Unsupported file type: {ext or '[no extension]'}")

    def _build_prompt(self, user_input: str) -> str:
        if not self.attachments:
            return user_input
        chunks = []
        for name, text in self.attachments:
            chunks.append(f"===== ATTACHMENT: {name} =====\n{text}")
        return (
            f"{user_input}\n\n"
            "Use the attached material as evidence. Distinguish source claims, "
            "inference, contradiction and uncertainty. Do not treat an attachment as automatically true.\n\n"
            + "\n\n".join(chunks)
        )

    def send(self) -> None:
        user_input = self.input_box.get("1.0", "end").strip()
        if not user_input and not self.attachments:
            return
        mode = self.mode_selector.get()
        provider_name = self.provider.get()
        api_key = self.api_key.get().strip()
        github_token = self.github_token.get().strip()
        repository = self.repository.get().strip()
        model = self.model.get().strip()
        if mode == "Agent / Tools" and not api_key:
            messagebox.showwarning("Missing API key", f"Enter the {provider_name} API key.")
            return
        if not github_token and mode == "Agent / Tools":
            messagebox.showwarning("Missing token", "Agent mode needs a GitHub token for repository tools.")
            return
        prompt = self._build_prompt(user_input or "Analyze the attached research material.")
        self._clear_input()
        self._append("YOU", prompt[:12000] + ("\n...[display truncated]" if len(prompt) > 12000 else ""))
        self.status.configure(text="ANNE is processing…")
        threading.Thread(
            target=self._worker,
            args=(prompt, api_key, github_token, repository, model, provider_name, mode, self.synthesis.get()),
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
        mode: str,
        use_synthesis: bool,
    ) -> None:
        try:
            if mode == "Pipeline First":
                state = run_pipeline(user_input)
                payload: dict[str, object] = {
                    "mode": "Pipeline First",
                    "llm_used": False,
                    "action": state.action,
                    "output": state.output,
                    "uncertainty": state.uncertainty,
                    "hypothesis_rankings": state.hypothesis_rankings,
                    "alternatives_preserved": len(state.low_prob_preserved),
                }
                if use_synthesis:
                    if not api_key:
                        raise ValueError("Optional Gemini synthesis is enabled, but no API key is configured.")
                    provider = GeminiProvider(api_key=api_key, model=model)
                    synthesis_prompt = (
                        "ANNE PIPELINE RESULT:\n"
                        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
                        "SOURCE INPUT:\n"
                        f"{user_input}\n\n"
                        "Analyze this evidence critically. Look especially for a useful insight, "
                        "contradiction, hidden assumption, or alternative interpretation that the "
                        "deterministic pipeline may not expose. Clearly label inference and uncertainty."
                    )
                    payload["synthesis"] = provider.ask(synthesis_prompt)
                    payload["llm_used"] = True
                self.result_queue.put(("pipeline", payload))
                return

            provider = GeminiProvider(api_key=api_key, model=model) if provider_name == "Gemini" else OpenRouterProvider(api_key=api_key, model=model)
            memory = GitHubMemory(token=github_token, repository=repository)
            agent = AnneAgent(provider, memory, workspace=ROOT)
            result = agent.run(user_input)
            self.result_queue.put(("agent", result))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def _poll_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "pipeline":
                    data = payload
                    synthesis = str(data.get("synthesis", "")).strip() if isinstance(data, dict) else ""
                    text = json.dumps(data, ensure_ascii=False, indent=2)
                    if synthesis:
                        text += f"\n\n===== OPTIONAL GEMINI ANALYSIS =====\n{synthesis}"
                    self._append("ANNE", text)
                    self.status.configure(text="Ready — pipeline completed.")
                elif kind == "agent":
                    result = payload
                    tools = ", ".join(result.tools_used) if result.tools_used else "none"
                    self._append(
                        "ANNE",
                        f"{result.response}\n\n[Tools: {tools}]\n"
                        f"[Learning saved: {result.memory_path} | confidence={result.confidence:.2f}]",
                    )
                    self.status.configure(text="Ready — agent completed.")
                else:
                    self._append("SYSTEM ERROR", str(payload))
                    self.status.configure(text="Error — check configuration or input files.")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneTinker().mainloop()
