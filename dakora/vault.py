from __future__ import annotations
from typing import Dict, Optional
from pathlib import Path
import yaml
from threading import RLock

from .renderer import Renderer
from .registry.local import LocalRegistry
from .model import TemplateSpec
from .exceptions import ValidationError, RenderError, TemplateNotFound, DakoraError
from .logging import Logger

class Vault:
    """
    Public API.
    - load templates from local dir
    - render with validated variables
    - optional logging
    - hot-reload via invalidate_cache()
    """
    def __init__(self, config_path: str | None = None, prompt_dir: str | None = None):
        if not (config_path or prompt_dir):
            raise DakoraError("pass config_path or prompt_dir")
        self.config = self._load_config(config_path) if config_path else {"prompt_dir": prompt_dir, "logging": {"enabled": False}}
        self.registry = LocalRegistry(self.config["prompt_dir"])
        self.renderer = Renderer()
        self.logger = Logger(self.config["logging"]["db_path"]) if self.config.get("logging", {}).get("enabled") else None
        self._cache: Dict[str, TemplateSpec] = {}
        self._lock = RLock()

    @staticmethod
    def _load_config(path: str) -> Dict:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if "prompt_dir" not in data:
            raise DakoraError("dakora.yaml missing prompt_dir")
        if "logging" not in data:
            data["logging"] = {"enabled": False}
        return data

    def list(self):
        return list(self.registry.list_ids())

    def invalidate_cache(self):
        with self._lock:
            self._cache.clear()

    def get_spec(self, template_id: str) -> TemplateSpec:
        with self._lock:
            if template_id in self._cache:
                return self._cache[template_id]
            spec = self.registry.load(template_id)
            self._cache[template_id] = spec
            return spec

    # public surface used by apps
    def get(self, template_id: str) -> "TemplateHandle":
        spec = self.get_spec(template_id)
        return TemplateHandle(self, spec)

class TemplateHandle:
    def __init__(self, vault: Vault, spec: TemplateSpec):
        self.vault = vault
        self.spec = spec

    @property
    def id(self): return self.spec.id
    @property
    def version(self): return self.spec.version
    @property
    def inputs(self): return self.spec.inputs

    def render(self, **kwargs) -> str:
        try:
            vars = self.spec.coerce_inputs(kwargs)
        except Exception as e:
            raise ValidationError(str(e)) from e
        try:
            return self.vault.renderer.render(self.spec.template, vars)
        except Exception as e:
            raise RenderError(str(e)) from e

    # optional logging helper
    def run(self, func, **kwargs):
        """
        Execute a call with logging.
        Usage:
            out = tmpl.run(lambda prompt: call_llm(prompt), input_text="...")
        """
        vars = self.spec.coerce_inputs(kwargs)
        prompt = self.vault.renderer.render(self.spec.template, vars)
        rec = {"inputs": vars, "output": None, "cost": None, "latency_ms": None}
        # no timing here; defer to app or use logging.run context
        out = func(prompt)
        rec["output"] = out
        if self.vault.logger:
            self.vault.logger.write(self.id, self.version, rec["inputs"], rec["output"])
        return out