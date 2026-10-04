"""Counts the words, lines and characters in a text. Reads one JSON object on stdin, prints one on stdout.

Input:  {"text": "hello there\nworld"}
Output: {"words": 3, "lines": 2, "characters": 17, "text": "3 words, 2 lines, 17 characters"}  or  {"error": "..."}
"""

import json
import sys


def main() -> None:
    try:
        text = json.load(sys.stdin)["text"]
        if not isinstance(text, str):
            raise TypeError
    except (KeyError, TypeError, ValueError):
        print(json.dumps({"error": "Give text as a string."}))
        return
    words, lines, characters = len(text.split()), len(text.splitlines()), len(text)
    print(json.dumps({
        "words": words,
        "lines": lines,
        "characters": characters,
        "text": f"{words} words, {lines} lines, {characters} characters",
    }))


main()
