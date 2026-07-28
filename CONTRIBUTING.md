# Contributing to ANNE

Thank you for your interest in contributing to the ANNE research platform.

## Ways to Contribute

- Architectural critique and alternative designs
- Implementation of new stages, memory backends, or evaluation protocols
- Formal benchmarks (especially hallucination reduction)
- Documentation improvements
- Research questions and literature notes

## Development Setup

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
pip install -e ".[dev]"
pre-commit install
```

## Code Standards

- Python 3.12+
- Type hints required
- Docstrings for public APIs
- Ruff + mypy clean
- Tests for new behavior

## Pull Request Process

1. Open an issue first for non-trivial changes.
2. Keep PRs focused.
3. Update documentation and tests.
4. Reference related research/decision logs when applicable.

## Research Contributions

New experimental results, negative results, and open questions are highly valued.
Please place literature notes under `research/literature/` and decision proposals under `research/decision_logs/`.
