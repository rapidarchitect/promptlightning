import typer, sys, time
from pathlib import Path
import yaml
from .vault import Vault
from .watcher import Watcher

app = typer.Typer(add_completion=False)

@app.command()
def init():
    root = Path.cwd()
    (root / "prompts").mkdir(exist_ok=True, parents=True)
    cfg = {
        "registry": "local",
        "prompt_dir": "./prompts",
        "logging": {"enabled": True, "backend": "sqlite", "db_path": "./promptvault.db"},
    }
    (root / "promptvault.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    example = {
        "id": "summarizer",
        "version": "1.0.0",
        "description": "Summarize text into exactly 3 bullets.",
        "template": "Summarize the following into exactly 3 bullet points:\n\n{{ input_text }}\n",
        "inputs": {"input_text": {"type": "string", "required": True}},
    }
    (root / "prompts" / "summarizer.yaml").write_text(yaml.safe_dump(example, sort_keys=False, allow_unicode=True), encoding="utf-8")
    typer.echo("Initialized PromptVault project.")

@app.command()
def list():
    v = Vault("promptvault.yaml")
    for tid in v.list():
        typer.echo(tid)

@app.command()
def get(id: str):
    v = Vault("promptvault.yaml")
    tmpl = v.get(id)
    # print raw template without rendering
    sys.stdout.write(tmpl.spec.template)

@app.command()
def bump(id: str, patch: bool = False, minor: bool = False, major: bool = False):
    # naive semantic bump: finds the file containing id and rewrites version
    prompt_dir = Path(yaml.safe_load(Path("promptvault.yaml").read_text())["prompt_dir"])
    target = None
    for p in prompt_dir.rglob("*.y*ml"):
        data = yaml.safe_load(p.read_text()) or {}
        if data.get("id") == id:
            target = p
            ver = data.get("version", "0.0.1")
            x,y,z = [int(n) for n in ver.split(".")]
            if major: x,y,z = x+1,0,0
            elif minor: y,z = y+1,0
            else: z += 1
            data["version"] = f"{x}.{y}.{z}"
            p.write_text(yaml.safe_dump(data, sort_keys=False))
            typer.echo(f"Bumped {id} -> {data['version']}")
            break
    if not target:
        raise SystemExit(f"Template '{id}' not found")

@app.command()
def watch():
    v = Vault("promptvault.yaml")
    pd = Path(yaml.safe_load(Path("promptvault.yaml").read_text())["prompt_dir"]).resolve()
    typer.echo(f"Watching {pd} for changes. Ctrl+C to stop.")
    w = Watcher(pd, on_change=v.invalidate_cache)
    w.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        w.stop()