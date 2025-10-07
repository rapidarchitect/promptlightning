from __future__ import annotations
from typing import Any, Dict
from functools import lru_cache
from jinja2 import Environment, StrictUndefined, Template
import yaml

try:
    from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
    YAML_C_AVAILABLE = True
except ImportError:
    from yaml import SafeLoader, SafeDumper
    YAML_C_AVAILABLE = False

@lru_cache(maxsize=1000)
def _yaml_dump_cached(obj_repr: str) -> str:
    """Cached YAML serialization. Uses string repr as cache key."""
    obj = eval(obj_repr)
    if YAML_C_AVAILABLE:
        return yaml.dump(obj, Dumper=SafeDumper, sort_keys=False, allow_unicode=True).rstrip()
    return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True).rstrip()

def _yaml_dump(obj: Any) -> str:
    """YAML filter with caching for common objects."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return str(obj)

    try:
        obj_repr = repr(obj)
        if len(obj_repr) < 1000:
            return _yaml_dump_cached(obj_repr)
    except (TypeError, ValueError):
        pass

    if YAML_C_AVAILABLE:
        return yaml.dump(obj, Dumper=SafeDumper, sort_keys=False, allow_unicode=True).rstrip()
    return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True).rstrip()

def _default_filter(val: Any, dflt: str = "") -> Any:
    """Default filter for falsy values."""
    return val if val not in (None, "", [], {}) else dflt

def make_env() -> Environment:
    """Create optimized Jinja2 environment with caching enabled."""
    env = Environment(
        autoescape=False,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        cache_size=10000,
        auto_reload=False,
        optimized=True
    )
    env.filters["default"] = _default_filter
    env.filters["yaml"] = _yaml_dump
    return env

class Renderer:
    """High-performance template renderer with compilation caching."""

    def __init__(self) -> None:
        self.env = make_env()
        self._compile_cache: Dict[str, Template] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def compile(self, template_text: str) -> Template:
        """Compile and cache template for reuse.

        Args:
            template_text: Template string to compile

        Returns:
            Compiled Jinja2 template object
        """
        if template_text in self._compile_cache:
            self._cache_hits += 1
            return self._compile_cache[template_text]

        self._cache_misses += 1
        compiled = self.env.from_string(template_text)

        if len(self._compile_cache) < 10000:
            self._compile_cache[template_text] = compiled

        return compiled

    def precompile(self, template_text: str) -> Template:
        """Pre-compile template for later use.

        This method is useful for warming up the cache during initialization.

        Args:
            template_text: Template string to pre-compile

        Returns:
            Compiled template object
        """
        return self.compile(template_text)

    def render(self, template_text: str, variables: Dict[str, Any]) -> str:
        """Render template with variables using cached compilation.

        Args:
            template_text: Template string
            variables: Variables to pass to template

        Returns:
            Rendered template string

        Raises:
            RuntimeError: If template rendering fails
        """
        try:
            tmpl = self.compile(template_text)
            return tmpl.render(**variables)
        except Exception as e:
            raise RuntimeError(f"render error: {e}") from e

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache metrics
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0.0

        return {
            "cache_size": len(self._compile_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "max_cache_size": 10000
        }

    def clear_cache(self) -> None:
        """Clear compilation cache and reset statistics."""
        self._compile_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
