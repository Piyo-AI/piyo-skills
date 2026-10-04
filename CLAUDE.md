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
It refuses a package that fails `validate_package` (licence, `SETUP.md`, tools, layout, script checks, secrets; the rules and their reasons are in that module), and prints reviewer warnings. CI is `.github/workflows/validate.yml`; it checks out the app repo next to this one. The index format is in `../PiyoAI/PLAN.md` section 5.

## Layout

```
index.json     catalog index the Piyo app reads (generated)
curation.json  maintainer-owned: badge, category, revoked versions and external (pinned Git) sources per skill
scripts/       build_index.py
skills/        one folder per skill package
templates/     starter skills (instructions only, Python, TypeScript); not in the index, but `build_index.py` validates
               them with the same rules, so a template that stops passing fails CI
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

Rules a catalog skill must meet (CI enforces them through the app's `core/piyo/skills/validate.py`; run `build_index.py --check` before opening a pull request):

- Folder name equals the `name` in frontmatter (lowercase letters, digits, single dashes).
- Declares an OSI-approved `license`, and lists every tool it needs in `requires.tools`. Request the minimum.
- Has a `SETUP.md`. A skill that automates a service against its terms (for example WhatsApp Web) must say so
  plainly in `SETUP.md`.
- No secrets, tokens or personal data anywhere in the package. Secrets are named in `requires.secrets` and
  injected at run time from the keychain.
- Instructions must not try to bypass confirmations or the permission gate; the gate wins regardless.
- Keep packages small; no binaries, no vendored dependencies (declare them in `runtime`).

## Working in this repo

- The index entry schema (currently 2) is defined in `PiyoAI/PLAN.md` section 5. Change it there first, then in
  `build_index.py` and the app's `core/piyo/skills/catalog.py`. Badges, categories, revocations and external
  sources live in `curation.json`, never in a skill's own files; only maintainers edit it. **`index.json.sig` is the maintainer's Ed25519 signature over `index.json`** (`scripts/sign_index.py`, key in the OS keychain, scheme in `core/piyo/skills/signing.py`); every change to the index needs `build_index.py` and then `sign_index.py sign`, and the app refuses an unsigned or stale catalog. Never try to produce a signature in CI or print, log or commit the private key. An external skill
  needs `source` (GitHub URL, full commit hash, optional `subpath`) and the build fetches it, so `--check` needs
  network and `git` when one is listed.
- `.github/CODEOWNERS` makes @sunaram the reviewer of everything, and of `curation.json`, `index.json`, `scripts/` and `.github/` in particular; `CONTRIBUTING.md` is the guide for authors, so keep it in step with `validate.py` when rules change. LF line endings (`.gitattributes`). MIT licence.
- Do not commit or push unless asked. Changes here are separate from the app repo's history.
