# Piyo Skills

The official catalog of skills for [Piyo AI](https://github.com/Piyo-AI/PiyoAI).

A skill is a folder with a `SKILL.md` (instructions for the agent) and a `SETUP.md` (setup guide for the user),
plus optional Python or JS/TS scripts. See the skill system section of the Piyo AI plan for the full format.

> Status: scaffold. The catalog index (`index.json`) is empty; submission rules, validation CI and signing
> are coming in a later phase.

## Layout

```
index.json     # catalog index consumed by the Piyo app
skills/        # skill packages
LICENSE        # MIT
```

All catalog skills must declare an open-source license.
