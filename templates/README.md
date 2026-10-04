# Skill templates

Starting points for a new skill. Each folder is a complete, working skill.

| Folder | What it shows |
|---|---|
| `my-instructions-skill` | Instructions only, no tools: the simplest skill |
| `my-python-skill` | A Python script run by `skill.run_script` (JSON in, JSON out) |
| `my-typescript-skill` | The same in TypeScript, run in Deno's sandbox |

To use one:

1. Copy the folder to `skills/<your-skill-name>/`.
2. Change `name` in `SKILL.md` to your skill's name (lowercase, dashes) so it equals the folder name, and set
   `author`, `description`, `version` and the instructions. Rewrite `SETUP.md` for your skill.
3. Delete the comments (`<!-- ... -->` and `#` lines) you do not need.
4. Run `uv run --project ../PiyoAI/core python scripts/build_index.py` and fix what it lists.

The full guide is [`docs/skill-authoring.md`](https://github.com/Piyo-AI/PiyoAI/blob/main/docs/skill-authoring.md)
in the app repo. These templates are checked by the same rules as a submission on every CI run, so they stay
valid.

They are not listed in the catalog: only `skills/` is.
