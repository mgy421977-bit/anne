# ANNE Persistent Memory

This folder is ANNE's first GitHub-backed long-term memory store.

Each interaction is saved as a separate timestamped JSON document by the Windows Tinker application.

Memory fields:
- `user_input`: the incoming task or message.
- `response`: ANNE's answer.
- `learning`: reusable durable learning extracted by ANNE.
- `confidence`: ANNE's self-estimated confidence from 0 to 1.
- `timestamp`: UTC creation time.

## Safety rules

1. API keys, GitHub tokens, passwords, and secrets must never be written here.
2. Memory is context, not ground truth; ANNE must validate it before relying on it.
3. New code changes should be proposed and tested separately before merging.
4. This memory is experimental and should not be treated as evidence of persistent consciousness.
