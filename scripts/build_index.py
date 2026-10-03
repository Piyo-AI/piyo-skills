"""Builds index.json from skills/*/ so the index can never drift from the packages.

The skill format and the package hash live in the Piyo app repo; this script imports them instead of copying
them. Run it with the app's Python environment:

    uv run --project ../PiyoAI/core python scripts/build_index.py          # rewrite index.json
    uv run --project ../PiyoAI/core python scripts/build_index.py --check  # fail if index.json is stale (CI)

Index format: PiyoAI/PLAN.md section 5, "Catalog index".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from piyo.skills.install import package_hash, permissions_of
from piyo.skills.manifest import SkillError, load_skill_dir

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 1
MAX_PACKAGE_BYTES = 2 * 1024 * 1024


def entry_for(path: Path) -> dict:
    skill = load_skill_dir(path, "catalog")
    m = skill.manifest
    problems = []
    if not m.license:
        problems.append("declare a license in SKILL.md")
    if not skill.has_setup:
        problems.append("add a SETUP.md")
    files = [p for p in path.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    if size > MAX_PACKAGE_BYTES:
        problems.append(f"package is {size} bytes (limit {MAX_PACKAGE_BYTES})")
    if problems:
        raise SkillError("; ".join(problems))
    return {
        "name": m.name,
        "version": m.version,
        "description": m.description,
        "author": m.author,
        "license": m.license,
        "path": f"skills/{path.name}",
        "sha256": package_hash(path),
        "files": len(files),
        "size": size,
        "permissions": permissions_of(skill),
        "integrations": m.requires.integrations,
        "secrets": m.requires.secrets,
        "model": m.requires.model.model_dump(exclude_defaults=True),
    }


def build(root: Path) -> tuple[dict, dict[str, str]]:
    entries, errors = [], {}
    folders = sorted(p for p in (root / "skills").iterdir() if p.is_dir() and not p.name.startswith("."))
    for folder in folders:
        try:
            entries.append(entry_for(folder))
        except (SkillError, OSError, UnicodeDecodeError) as e:
            errors[folder.name] = str(e)
    return {"schema": SCHEMA, "skills": entries}, errors


def render(index: dict) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if index.json is out of date")
    args = parser.parse_args()

    index, errors = build(ROOT)
    for name, why in errors.items():
        print(f"skills/{name}: {why}", file=sys.stderr)
    if errors:
        return 1
    text = render(index)
    target = ROOT / "index.json"
    if args.check:
        current = target.read_text(encoding="utf-8") if target.is_file() else ""
        if current != text:
            print("index.json is out of date; run scripts/build_index.py", file=sys.stderr)
            return 1
        return 0
    with target.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"index.json: {len(index['skills'])} skill(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
