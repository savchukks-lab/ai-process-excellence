from __future__ import annotations

import faulthandler
import importlib
import sys
from pathlib import Path

faulthandler.enable()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def import_with_trace(module_name: str) -> None:
    print(f"before import {module_name}", flush=True)
    importlib.import_module(module_name)
    print(f"after import {module_name}", flush=True)


def main() -> None:
    print(f"python {sys.version}", flush=True)
    for module_name in ["streamlit", "pandas", "numpy", "openpyxl", "altair", "deal_logic", "streamlit_app"]:
        import_with_trace(module_name)
    print("import smoke test complete", flush=True)


if __name__ == "__main__":
    main()
