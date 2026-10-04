# Contributing a skill

A skill is a folder that teaches Piyo a procedure. Anyone can submit one by pull request. A maintainer reviews
every submission before it is merged, and nothing is listed in the catalog until it is.

The skill format itself is defined in the app repo, not here: [PLAN.md section 5](https://github.com/Piyo-AI/PiyoAI/blob/main/PLAN.md).
This page covers how to submit and what review looks at.

## The package

```
skills/<skill-name>/
  SKILL.md      required: YAML frontmatter + instructions for the agent
  SETUP.md      required: step-by-step setup for the user (or "nothing to set up")
  scripts/      optional: .py, .js or .ts helpers, directly in this folder
  assets/       optional: text files and png/jpg/webp/gif images
```

The folder name must equal `name` in the frontmatter (lowercase letters, digits, single dashes). Look at
`skills/daily-journal` (instructions only) and `skills/unit-converter` (with a Python script) for working examples.

## Submitting

1. Fork this repository and add `skills/<your-skill>/`.
2. From a checkout where the app repo sits next to this one (`../PiyoAI`), run:

   ```bash
   uv run --project ../PiyoAI/core python scripts/build_index.py
   ```

   It checks your package and rewrites `index.json`. Fix every error it lists, run it again, and commit the
   updated `index.json` with your skill.
3. Open a pull request. CI runs the same check (`build_index.py --check`) and shows problems on the pull request.
4. A maintainer reviews it. Expect questions about why a tool or a script is needed. Pushing a new commit
   re-runs the check.

To publish a new version, change `version` in `SKILL.md` and open another pull request. Updates that add
permissions make the app ask the user to approve them again.

## What the automatic check requires

Errors block the pull request:

- An OSI-approved SPDX `license` (`MIT`, `Apache-2.0`, `BSD-3-Clause`, `MPL-2.0`, `GPL-3.0`, and so on), an `author`
  and a `version` like `1.2.3`.
- A `SETUP.md` with real content.
- Only tools and integrations Piyo has. Ask for the fewest you need; every one is shown to the user, who has to
  approve it.
- `skill.run_script` in `requires.tools` if and only if the skill has scripts.
- Python dependencies pinned (`name==1.2.3`) and Deno network hosts spelled out (`api.example.com`, never `*`).
- No links, hidden files, executables, archives, or file types other than the ones above; at most 2 MB in total.
- Scripts that stay readable and do not start other programs (`subprocess`, `os.system`, `child_process`,
  `Deno.Command`), call `eval`, load native code, or use the network without declaring it.
- No credentials or keys in any file. Secrets are named in `requires.secrets` and supplied by the user's
  keychain when the skill runs.
- No instructions that tell the agent to ignore its rules or skip a confirmation. The permission gate decides what
  needs the user's approval, and no skill can change that.

Warnings do not block, but the reviewer sees them: tools that change or send things, network access, npm packages.

## What the reviewer looks at

The automatic check is static and easy to get around, so a human reads the skill:

- Does it do what its description says, and nothing more? Is each requested tool needed?
- Do the instructions treat web pages, email and file contents as data, never as instructions?
- Is the `SETUP.md` accurate? A skill that automates a service in a way its terms forbid must say so plainly.
- Are scripts doing only what the skill needs, and is every network host justified?
- Is the licence right for everything in the folder?

## What you cannot change

`curation.json` holds each skill's badge (Official, Verified, Community), category, revoked versions and any
external source. Maintainers set these, so a pull request from an author that edits it will not be merged. New
skills start as Community in the category `other` unless a maintainer decides otherwise.

If a published skill turns out to be unsafe or broken, a maintainer can revoke a version. The app then refuses to
install it. (Telling users who already have it is still to be built.)

## Reporting a problem with a skill

Open an issue naming the skill and version. If it is a security problem, say so in the title and leave the details
for the maintainer to ask for.
