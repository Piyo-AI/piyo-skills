# piyo-skills (skill catalog repo)

The public catalog of skills for [Piyo AI](https://github.com/Piyo-AI/PiyoAI). **Status: early.** `skills/` holds one sample
skill, `daily-journal`, for testing install; `index.json` is generated from it. Submission rules, validation CI and
signing are Phase 5 work (see `../docs/phase-5-public-release.md`).

This repo contains data and skill packages only, plus one script, `scripts/build_index.py`, that generates `index.json`.
After changing anything under `skills/`, run it (and commit the result); CI will run it with `--check`:

```bash
uv run --project ../PiyoAI/core python scripts/build_index.py          # rewrite index.json
uv run --project ../PiyoAI/core python scripts/build_index.py --check  # fail if stale
```

The script imports the skill format and the package hash from the app's core, so the format is not copied here.
It refuses a skill with no `license` or no `SETUP.md`. The index format is in `../PiyoAI/PLAN.md` section 5.

## Layout

```
index.json     catalog index the Piyo app reads (generated)
scripts/       build_index.py
skills/        one folder per skill package
LICENSE        MIT
```

## A skill package

```
skills/<skill-name>/
  SKILL.md      required: YAML frontmatter + instructions for the agent
  SETUP.md      required for the catalog: step-by-step user setup (accounts, keys, OAuth)
  scripts/      optional Python or JS/TS helpers
  assets/       optional templates and examples
```

**The format is defined in the app repo, not here:** `../PiyoAI/PLAN.md` §5, implemented by
`../PiyoAI/core/piyo/skills/manifest.py`. Do not restate or fork it in this repo; link to it.

Rules a catalog skill must meet (CI will enforce them later; follow them now):

- Folder name equals the `name` in frontmatter (lowercase letters, digits, single dashes).
- Declares an OSI-approved `license`, and lists every tool it needs in `requires.tools`. Request the minimum.
- Has a `SETUP.md`. A skill that automates a service against its terms (for example WhatsApp Web) must say so
  plainly in `SETUP.md`.
- No secrets, tokens or personal data anywhere in the package. Secrets are named in `requires.secrets` and
  injected at run time from the keychain.
- Instructions must not try to bypass confirmations or the permission gate; the gate wins regardless.
- Keep packages small; no binaries, no vendored dependencies (declare them in `runtime`).

## Working in this repo

- `index.json` has no entry schema yet. Do not invent one ad hoc: define it in `PiyoAI/PLAN.md` first (Phase 5),
  then add entries.
- LF line endings (`.gitattributes`). MIT licence.
- Do not commit or push unless asked. Changes here are separate from the app repo's history.
