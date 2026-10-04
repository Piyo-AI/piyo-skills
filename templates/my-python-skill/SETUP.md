# Set up the text statistics skill

Nothing to set up: no accounts, keys or internet access.

## Try it

1. Say: "How many words are in this: the quick brown fox jumps over the lazy dog".
2. Piyo loads the skill and asks to run its script `text_stats.py`. Because you installed this skill, Piyo asks
   you to approve the script each time. Approve it.
3. Piyo answers with the exact counts.

## What this skill can do

- Run its own `text_stats.py` script, which only counts the text it is given.
- The script runs in its own Python environment with no network access and a 10 second limit.
