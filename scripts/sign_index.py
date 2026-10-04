"""Signs index.json so the Piyo app will accept the catalog. Run it on the maintainer's own machine.

    uv run --project ../PiyoAI/core python scripts/sign_index.py keygen          # once: make the key
    uv run --project ../PiyoAI/core python scripts/sign_index.py public          # the line to put in the app
    uv run --project ../PiyoAI/core python scripts/sign_index.py sign            # after build_index.py
    uv run --project ../PiyoAI/core python scripts/sign_index.py verify          # what CI runs on main
    uv run --project ../PiyoAI/core python scripts/sign_index.py export-key FILE # backup (keep it offline)
    uv run --project ../PiyoAI/core python scripts/sign_index.py import-key FILE # restore on a new machine

The private key lives in the OS keychain (service "piyo-catalog-signing") and is never written into this repo, a
log or a message. The app trusts the public keys in `PiyoAI/core/piyo/skills/signing.py` (`TRUSTED_KEYS`).
The signature scheme is documented in that module.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import os
import sys
from pathlib import Path

import keyring
from build_index import ROOT, build, render
from piyo.skills import signing

SERVICE = "piyo-catalog-signing"
ACCOUNT = "index-signing-key"
INDEX = ROOT / "index.json"
SIGNATURE = ROOT / "index.json.sig"


def load_private() -> bytes:
    stored = keyring.get_password(SERVICE, ACCOUNT)
    if not stored:
        sys.exit("There is no signing key on this machine. Run `keygen` (or `import-key`) first.")
    try:
        raw = base64.b64decode(stored, validate=True)
        signing.public_of(raw)
    except (binascii.Error, ValueError):
        sys.exit("The stored signing key is damaged. Restore it with `import-key`.")
    return raw


def describe(public: bytes) -> str:
    return f'"{signing.key_id(public)}": "{base64.b64encode(public).decode("ascii")}",'


def keygen(_: argparse.Namespace) -> int:
    if keyring.get_password(SERVICE, ACCOUNT):
        print("A signing key already exists here. Replacing it would lock out every installed app that trusts it.")
        print("Use `public` to see it, or delete the keychain entry by hand if you really mean to rotate.")
        return 1
    private, public = signing.generate()
    keyring.set_password(SERVICE, ACCOUNT, base64.b64encode(private).decode("ascii"))
    print("Made a signing key and stored it in this machine's keychain.")
    print("1. Add this line to TRUSTED_KEYS in PiyoAI/core/piyo/skills/signing.py and ship an app that has it:")
    print(f"   {describe(public)}")
    print("2. Back the key up now with `export-key FILE` and keep the file offline. Without it you cannot sign.")
    return 0


def public(_: argparse.Namespace) -> int:
    print(describe(signing.public_of(load_private())))
    return 0


def export_key(args: argparse.Namespace) -> int:
    target = Path(args.file)
    if target.exists():
        print(f"{target} already exists; not overwriting it.")
        return 1
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(base64.b64encode(load_private()).decode("ascii") + "\n")
    print(f"Wrote the private key to {target}. Keep it offline and never commit or share it.")
    return 0


def import_key(args: argparse.Namespace) -> int:
    if keyring.get_password(SERVICE, ACCOUNT):
        print("A signing key already exists here; not replacing it.")
        return 1
    try:
        raw = base64.b64decode(Path(args.file).read_text(encoding="utf-8").strip(), validate=True)
        key = signing.public_of(raw)
    except (OSError, binascii.Error, ValueError):
        print("That file does not hold a signing key.")
        return 1
    keyring.set_password(SERVICE, ACCOUNT, base64.b64encode(raw).decode("ascii"))
    print(f"Restored the signing key {signing.key_id(key)}.")
    return 0


def sign(_: argparse.Namespace) -> int:
    index, errors, _warnings = build(ROOT)
    if errors:
        print("The skills have problems; fix them with build_index.py first.", file=sys.stderr)
        return 1
    fresh = render(index).encode("utf-8")
    if not INDEX.is_file() or INDEX.read_bytes() != fresh:
        print("index.json is out of date. Run build_index.py first, so you sign what the skills really are.")
        return 1
    private = load_private()
    line = signing.sign(private, fresh)
    mine = signing.key_id(signing.public_of(private))
    if mine not in signing.TRUSTED_KEYS:
        print(f"Note: key {mine} is not in TRUSTED_KEYS yet, so installed apps will refuse this signature.")
    with SIGNATURE.open("w", encoding="utf-8", newline="\n") as f:
        f.write(line)
    print(f"Signed index.json ({len(index['skills'])} skill(s)) with key {mine}. Commit index.json.sig with it.")
    return 0


def verify(_: argparse.Namespace) -> int:
    if not SIGNATURE.is_file():
        print("index.json.sig is missing. Run sign_index.py sign on the maintainer's machine and push it.")
        return 1
    try:
        signer = signing.verify(INDEX.read_bytes(), SIGNATURE.read_text(encoding="utf-8"))
    except signing.SignatureError as e:
        print(f"index.json.sig does not match index.json: {e}")
        return 1
    print(f"index.json is signed by trusted key {signer}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("keygen", keygen), ("public", public), ("sign", sign), ("verify", verify)):
        sub.add_parser(name).set_defaults(run=fn)
    for name, fn in (("export-key", export_key), ("import-key", import_key)):
        sub.add_parser(name).add_argument("file")
        sub.choices[name].set_defaults(run=fn)
    args = parser.parse_args()
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
