"""ANNE Windows Tinker — local/cloud models plus research-file attachments."""

from __future__ import annotations

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

from anne.agent.github_memory import GitHubMemory
from anne.agent.runtime import AnneAgent

DEFAULT_OR_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
DEFAULT_GEMINI_MODEL = "gemini-3.7-flash"
DEFAULT_OLLAMA_MODEL = "gemma3:4b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_CONTEXT_CHARS = 180_000
TEXT_EXTENSIONS = {
    ".txt", ".md", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".json",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".tsv", ".xml",
    ".html", ".css", ".sql", ".sh", ".bat", ".ps1", ".c", ".cpp", ".h",
    ".hpp", ".java", ".go", ".rs", ".swift", ".kt", ".log", ".tex",
}


class AnneTinker(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ANNE AI — Windows Tinker")
        # Keep the complete chat input visible on common 768px-tall Windows screens.
        self.geometry("1180x700")
        self.minsize(980, 600)
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.attachments: list[Path] = []
        self._build_ui()
        self._load_env_defaults()
        self._update_provider_fields()
        self.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        config = ttk.LabelFrame(root, text="Connection")
        config.pack(fill="x", pady=(0, 10))
        for column in (1, 3):
            config.columnconfigure(column, weight=1)

        ttk.Label(config, text="Provider").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.provider = ttk.Combobox(
            config,
            values=["Ollama Local", "Gemini", "OpenRouter Free"],
            state="readonly",
            width=20,
        )
        self.provider.grid(row=0, column=1, sticky="w", padx=8, pady=6)
        self.provider.bind("<<ComboboxSelected>>", lambda _event: self._update_provider_fields())

        self.key_label = ttk.Label(config, text="API key")
        self.key_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.api_key = ttk.Entry(config, show="*", width=62)
        self.api_key.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Ollama URL").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.base_url = ttk.Entry(config, width=42)
        self.base_url.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="GitHub token").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        self.github_token = ttk.Entry(config, show="*", width=62)
        self.github_token.grid(row=3, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Repository").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.repository = ttk.Entry(config, width=28)
        self.repository.grid(row=0, column=3, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Model").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        self.model = ttk.Entry(config, width=34)
        self.model.grid(row=1, column=3, sticky="ew", padx=8, pady=6)

        ttk.Label(config, text="Mode").grid(row=2, column=2, sticky="w", padx=8, pady=6)
        self.mode = ttk.Label(config, text="Pipeline-first cognitive runtime")
        self.mode.grid(row=2, column=3, sticky="w", padx=8, pady=6)

        self.connection_button = ttk.Button(config, text="Test connection", command=self.test_connection)
        self.connection_button.grid(row=3, column=2, sticky="w", padx=8, pady=6)

        self.status = ttk.Label(config, text="Ready", anchor="w")
        self.status.grid(row=4, column=0, columnspan=4, sticky="ew", padx=8, pady=(2, 8))

        research = ttk.LabelFrame(root, text="Research Files")
        research.pack(fill="x", pady=(0, 10))
        research.columnconfigure(0, weight=1)
        self.file_list = tk.Listbox(research, height=5, selectmode="extended")
        self.file_list.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=8, pady=8)
        button_col = ttk.Frame(research)
        button_col.grid(row=0, column=1, rowspan=2, sticky="ns", padx=(0, 8), pady=8)
        ttk.Button(button_col, text="Add files…", command=self.add_files).pack(fill="x", pady=(0, 5))
        ttk.Button(button_col, text="Remove selected", command=self.remove_selected_files).pack(fill="x", pady=5)
        ttk.Button(button_col, text="Clear files", command=self.clear_files).pack(fill="x", pady=5)
        ttk.Label(
            research,
            text="TXT / MD / code / JSON / CSV / PDF / DOCX  •  files are extracted locally and sent as research context",
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        chat_frame = ttk.LabelFrame(root, text="ANNE")
        chat_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.chat = scrolledtext.ScrolledText(chat_frame, wrap="word", font=("Segoe UI", 10))
        self.chat.pack(fill="both", expand=True, padx=8, pady=8)
        self.chat.configure(state="disabled")

        input_frame = ttk.Frame(root)
        input_frame.pack(fill="x")
        self.input_box = tk.Text(input_frame, height=4, wrap="word", font=("Segoe UI", 10))
        self.input_box.pack(side="left", fill="both", expand=True)
        self.input_box.bind("<Control-Return>", lambda _event: self.send())

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(button_frame, text="Send", command=self.send).pack(fill="x", pady=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self._clear_input).pack(fill="x")

        ttk.Label(
            root,
            text="Ctrl+Enter = Send | Attach an ATHENA/research file and ask ANNE to test assumptions, contradictions, uncertainty and missed alternatives.",
        ).pack(anchor="w", pady=(5, 0))

    def _load_env_defaults(self) -> None:
        self.provider.set(os.getenv("ANNE_PROVIDER", "Ollama Local"))
        self.api_key.insert(0, os.getenv("ANNE_API_KEY", os.getenv("OPENROUTER_API_KEY", "")))
        self.base_url.insert(0, os.getenv("ANNE_OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL))
        self.github_token.insert(0, os.getenv("GITHUB_TOKEN", ""))
        self.repository.insert(0, os.getenv("ANNE_REPOSITORY", "mgy421977-bit/anne"))
        self.model.insert(0, os.getenv("ANNE_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL))

    def _update_provider_fields(self) -> None:
        selected = self.provider.get()
        current = self.model.get().strip()
        if selected == "Ollama Local":
            self.key_label.configure(text="API key (not required)")
            self.base_url.configure(state="normal")
            self.mode.configure(text="Local model + ANNE cognitive runtime")
            if not current or current in (DEFAULT_OR_MODEL, DEFAULT_GEMINI_MODEL):
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL))
        elif selected == "Gemini":
            self.key_label.configure(text="Gemini API key")
            self.base_url.configure(state="disabled")
            self.mode.configure(text="Cloud model + ANNE cognitive runtime")
            if not current or current in (DEFAULT_OLLAMA_MODEL, DEFAULT_OR_MODEL):
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_GEMINI_MODEL", DEFAULT_GEMINI_MODEL))
        else:
            self.key_label.configure(text="OpenRouter API key")
            self.base_url.configure(state="disabled")
            self.mode.configure(text="Cloud model + tools + ANNE cognitive runtime")
            if not current or current in (DEFAULT_OLLAMA_MODEL, DEFAULT_GEMINI_MODEL):
                self.model.delete(0, "end")
                self.model.insert(0, os.getenv("ANNE_OPENROUTER_MODEL", DEFAULT_OR_MODEL))

    def _append(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{speaker}\n{text}\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _clear_input(self) -> None:
        self.input_box.delete("1.0", "end")

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Attach research files",
            filetypes=[
                ("Research files", "*.txt *.md *.rst *.py *.js *.ts *.json *.yaml *.yml *.toml *.csv *.tsv *.xml *.html *.css *.sql *.pdf *.docx"),
                ("All files", "*.*"),
            ],
        )
        for raw in paths:
            path = Path(raw)
            if path not in self.attachments:
                self.attachments.append(path)
                self.file_list.insert("end", str(path))
        self.status.configure(text=f"Attached research files: {len(self.attachments)}")

    def remove_selected_files(self) -> None:
        selected = list(self.file_list.curselection())
        for index in reversed(selected):
            self.file_list.delete(index)
            self.attachments.pop(index)
        self.status.configure(text=f"Attached research files: {len(self.attachments)}")

    def clear_files(self) -> None:
        self.attachments.clear()
        self.file_list.delete(0, "end")
        self.status.configure(text="Research files cleared.")

    @staticmethod
    def _extract_docx(path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        paragraphs: list[str] = []
        for paragraph in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            words = [node.text or "" for node in paragraph.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
            line = "".join(words).strip()
            if line:
                paragraphs.append(line)
        return "\n".join(paragraphs)

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
        return "\n\n".join(pages)

    @classmethod
    def _read_attachment(cls, path: Path) -> str:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"{path.name} exceeds the 4 MB attachment limit")
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return cls._extract_pdf(path)
        if suffix == ".docx":
            return cls._extract_docx(path)
        if suffix not in TEXT_EXTENSIONS:
            raise ValueError(f"Unsupported research file type: {suffix or '(no extension)'}")
        return path.read_text(encoding="utf-8", errors="replace")

    def _build_research_context(self) -> tuple[str, list[str]]:
        if not self.attachments:
            return "", []
        parts: list[str] = []
        used: list[str] = []
        remaining = MAX_CONTEXT_CHARS
        for path in self.attachments:
            text = self._read_attachment(path).strip()
            if not text:
                continue
            header = f"===== RESEARCH FILE: {path.name} =====\n"
            chunk = header + text
            if len(chunk) > remaining:
                chunk = chunk[:remaining] + "\n[TRUNCATED BY ANNE TINKER CONTEXT LIMIT]"
            parts.append(chunk)
            used.append(path.name)
            remaining -= len(chunk)
            if remaining <= 0:
                break
        return "\n\n".join(parts), used

    def _validate_send(self) -> tuple[str, str, str, str, str, str]:
        provider = self.provider.get()
        model = self.model.get().strip()
        api_key = self.api_key.get().strip()
        base_url = self.base_url.get().strip()
        github_token = self.github_token.get().strip()
        repository = self.repository.get().strip()
        if provider != "Ollama Local" and not api_key:
            raise ValueError(f"Enter the {provider} API key.")
        if not github_token:
            raise ValueError("Enter a GitHub token with Contents permission so ANNE can use its durable memory.")
        if not model:
            raise ValueError("Enter a model name.")
        if provider == "Ollama Local" and not base_url:
            raise ValueError("Enter the Ollama base URL.")
        return provider, model, api_key, base_url, github_token, repository

    def send(self) -> None:
        user_input = self.input_box.get("1.0", "end").strip()
        if not user_input:
            return
        try:
            provider, model, api_key, base_url, github_token, repository = self._validate_send()
            external_context, used_files = self._build_research_context()
        except Exception as exc:
            messagebox.showwarning("ANNE Tinker", str(exc))
            return
        self._clear_input()
        self._append("YOU", user_input)
        if used_files:
            self._append("RESEARCH FILES", "\n".join(f"• {name}" for name in used_files))
        self.status.configure(text=f"ANNE is reasoning with {provider}…")
        threading.Thread(
            target=self._worker,
            args=(user_input, external_context, api_key, github_token, repository, model, base_url, provider),
            daemon=True,
        ).start()

    def _worker(
        self,
        user_input: str,
        external_context: str,
        api_key: str,
        github_token: str,
        repository: str,
        model: str,
        base_url: str,
        provider_name: str,
    ) -> None:
        try:
            if provider_name == "Ollama Local":
                from anne.providers.ollama import OllamaProvider
                provider = OllamaProvider(base_url=base_url, model=model)
            elif provider_name == "Gemini":
                from anne.providers.gemini import GeminiProvider
                provider = GeminiProvider(api_key=api_key, model=model)
            else:
                from anne.providers.openrouter import OpenRouterProvider
                provider = OpenRouterProvider(api_key=api_key, model=model)
            memory = GitHubMemory(token=github_token, repository=repository)
            agent = AnneAgent(provider, memory, workspace=ROOT)
            result = agent.run(user_input, external_context=external_context)
            self.result_queue.put(("ok", result))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def test_connection(self) -> None:
        provider_name = self.provider.get()
        model = self.model.get().strip()
        base_url = self.base_url.get().strip()
        api_key = self.api_key.get().strip()
        try:
            if provider_name == "Ollama Local":
                from anne.providers.ollama import OllamaProvider
                provider = OllamaProvider(base_url=base_url, model=model)
                if not provider.ping():
                    raise RuntimeError("Ollama is not reachable. Start Ollama and confirm the base URL.")
                self.status.configure(text=f"Ollama OK — {model}")
            elif provider_name == "Gemini":
                from anne.providers.gemini import GeminiProvider
                provider = GeminiProvider(api_key=api_key, model=model)
                reply = provider.ask("Reply with exactly: ANNE TEST OK")
                self.status.configure(text=f"Gemini OK — {reply.strip()[:60]}")
            else:
                from anne.providers.openrouter import OpenRouterProvider
                provider = OpenRouterProvider(api_key=api_key, model=model)
                data = provider.chat([{"role": "user", "content": "Reply with exactly: ANNE TEST OK"}])
                reply = str((data.get("choices") or [{}])[0].get("message", {}).get("content") or "")
                self.status.configure(text=f"OpenRouter OK — {reply.strip()[:60]}")
        except Exception as exc:
            self.status.configure(text="Connection test failed.")
            messagebox.showerror("ANNE connection test", str(exc))

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
                    self.status.configure(text="Ready — response, cognition review and memory completed.")
                else:
                    self._append("SYSTEM ERROR", str(payload))
                    self.status.configure(text="Error — check provider, Ollama, GitHub permissions, file format or network.")
        except queue.Empty:
            pass
        self.after(100, self._poll_results)


if __name__ == "__main__":
    AnneTinker().mainloop()
