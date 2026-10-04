"""Builds index.json from skills/*/ so the index can never drift from the packages.

The skill format and the package hash live in the Piyo app repo; this script imports them instead of copying
them. Run it with the app's Python environment:

    uv run --project ../PiyoAI/core python scripts/build_index.py          # rewrite index.json
    uv run --project ../PiyoAI/core python scripts/build_index.py --check  # fail if index.json is stale (CI)

Index format: PiyoAI/PLAN.md section 5, "Catalog index". Badge, category, revocation and external sources come
from curation.json (maintainer-owned), never from a skill's own files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from piyo.skills.install import package_hash, permissions_of
from piyo.skills.manifest import SkillError
from piyo.skills.validate import validate_package

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 2
CATEGORIES = ("productivity", "communication", "web", "files", "developer", "media", "utilities", "other")
BADGES = ("official", "verified", "community")
_SHA = re.compile(r"[0-9a-f]{40}")
_GITHUB = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def entry_for(path: Path, curated: dict, location: dict, warnings: list[str]) -> dict:
    skill, report = validate_package(path)
    problems = list(report.errors)
    warnings += [f"{path.name}: {w}" for w in report.warnings]
    if curated.get("category", "other") not in CATEGORIES:
        problems.append(f"curation.json: category must be one of {', '.join(CATEGORIES)}")
    if curated.get("badge", "community") not in BADGES:
        problems.append(f"curation.json: badge must be one of {', '.join(BADGES)}")
    revoked = curated.get("revoked", [])
    if not isinstance(revoked, list) or not all(
        isinstance(r, dict) and isinstance(r.get("version"), str) and isinstance(r.get("reason"), str) and r["reason"]
        for r in revoked
    ):
        problems.append('curation.json: revoked must be a list of {"version": ..., "reason": ...} ("*" is every version)')
    if problems or skill is None:
        raise SkillError("\n  ".join(problems))
    m = skill.manifest
    files = [p for p in path.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    return {
        "name": m.name,
        "version": m.version,
        "description": m.description,
        "author": m.author,
        "license": m.license,
        **location,
        "category": curated.get("category", "other"),
        "badge": curated.get("badge", "community"),
        "revoked": revoked,
        "sha256": package_hash(path),
        "files": len(files),
        "size": size,
        "permissions": permissions_of(skill),
        "integrations": m.requires.integrations,
        "secrets": m.requires.secrets,
        "model": m.requires.model.model_dump(exclude_defaults=True),
    }


def load_curation(root: Path) -> dict[str, dict]:
    target = root / "curation.json"
    if not target.is_file():
        return {}
    doc = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("skills", {}), dict):
        raise SkillError('curation.json must be {"skills": {"<name>": {...}}}')
    return doc.get("skills", {})


def fetch_external(name: str, source: dict, into: Path) -> tuple[Path, dict]:
    """Check out an external skill at its pinned commit; returns the package folder and its index location."""
    url, commit, sub = source.get("url", ""), source.get("commit", ""), source.get("subpath", "")
    if not _GITHUB.fullmatch(url):
        raise SkillError("source.url must be https://github.com/<owner>/<repo>")
    if not _SHA.fullmatch(commit):
        raise SkillError("source.commit must be a full 40-character commit hash (no branches or tags)")
    if not isinstance(sub, str) or ".." in PurePosixPath(sub).parts or sub.startswith(("/", "\\")):
        raise SkillError("source.subpath must be a relative folder inside the repository")
    repo = into / name
    git = ["git", "-c", "core.symlinks=false", "-C", str(repo)]
    try:
        repo.mkdir()
        for cmd in (
            ["git", "init", "-q", str(repo)],
            [*git, "fetch", "-q", "--depth=1", url + ".git", commit],
            [*git, "checkout", "-q", "FETCH_HEAD"],
        ):
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        raise SkillError(f"could not fetch {url} at {commit[:7]}: {getattr(e, 'stderr', b'').decode(errors='replace').strip() or e}") from None
    folder = (repo / sub) if sub else repo
    return folder, {"path": sub, "source": {"type": "git", "url": url, "commit": commit, "subpath": sub}}


def build(root: Path) -> tuple[dict, dict[str, str], list[str]]:
    entries, errors, warnings = [], {}, []
    try:
        curation = load_curation(root)
    except (SkillError, ValueError, OSError) as e:
        return {"schema": SCHEMA, "skills": []}, {"curation.json": str(e)}, []
    folders = sorted(p for p in (root / "skills").iterdir() if p.is_dir() and not p.name.startswith("."))
    names = {f.name for f in folders}
    for name, cur in curation.items():
        if not isinstance(cur, dict):
            errors[name] = "curation entry must be an object"
        elif "source" not in cur and name not in names:
            errors[name] = "curation.json lists a skill that is not in skills/ and has no source"
        elif "source" in cur and name in names:
            errors[name] = "skills/ has this skill and curation.json gives it an external source"
    with tempfile.TemporaryDirectory() as tmp:
        for folder in folders:
            if folder.name in errors:
                continue
            try:
                entries.append(entry_for(folder, curation.get(folder.name, {}), {"path": f"skills/{folder.name}"}, warnings))
            except (SkillError, OSError, UnicodeDecodeError) as e:
                errors[folder.name] = str(e)
        for name, cur in curation.items():
            if name in errors or "source" not in cur:
                continue
            try:
                folder, location = fetch_external(name, cur["source"], Path(tmp))
                entry = entry_for(folder, cur, location, warnings)
                if entry["name"] != name:
                    raise SkillError(f"the skill calls itself {entry['name']!r}, not {name!r}")
                entries.append(entry)
            except (SkillError, OSError, UnicodeDecodeError) as e:
                errors[name] = str(e)
    entries.sort(key=lambda e: e["name"])
    return {"schema": SCHEMA, "skills": entries}, errors, warnings


def render(index: dict) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if index.json is out of date")
    args = parser.parse_args()

    index, errors, warnings = build(ROOT)
    github = os.environ.get("GITHUB_ACTIONS") == "true"  # shows the lines as annotations on the pull request
    for warning in warnings:
        print(f"::warning::{warning}" if github else f"warning: {warning}", file=sys.stderr)
    for name, why in errors.items():
        text = f"::error::{name}: {why}".replace("\n", "%0A") if github else f"{name}:\n  {why}"
        print(text, file=sys.stderr)
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
