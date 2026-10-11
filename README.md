# py-aether-forge

A py-game tower defence game in hommage to the old warcraft 3 td maps - with a new twist.

## Voraussetzungen

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

- Qt 6 (wird automatisch über uv installiert)


## Setup

```bash
uv sync
uv run python -m py_aether_forge
```

## Framework

Dieses Projekt verwendet **PySide6**.

## Projektstruktur

```
py-aether-forge/
├── src/
│   └── py_aether_forge/
│       ├── __init__.py
│       ├── __main__.py
│       └── ui/
│           └── main_window.py
├── tests/
├── pyproject.toml
└── README.md
```