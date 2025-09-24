from __future__ import annotations
from typing import Iterable
from pathlib import Path
import yaml
from ..model import TemplateSpec
from ..exceptions import TemplateNotFound

class LocalRegistry:
    def __init__(self, prompt_dir: str | Path) -> None:
        self.root = Path(prompt_dir).resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"prompt_dir not found: {self.root}")

    def list_ids(self) -> Iterable[str]:
        for p in self.root.rglob("*.y*ml"):
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                tid = data.get("id")
                if tid:
                    yield tid
            except Exception:
                continue

    def load(self, template_id: str) -> TemplateSpec:
        for p in self.root.rglob("*.y*ml"):
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                if data.get("id") == template_id:
                    return TemplateSpec.model_validate(data)
            except Exception:
                continue
        raise TemplateNotFound(template_id)