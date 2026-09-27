"""Issue or revoke a scoped API key. The database stores only a hash.

From the repo root:

    python scripts/issue_api_credential.py --email you@example.com --label local-load-test --scopes data,llm
    python scripts/issue_api_credential.py --revoke 1

The raw key is printed once. API_SECRET_KEY is the local docs password and is not a credential.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.models import create_tables
from database.repository import get_account_by_email, issue_api_credential, revoke_api_credential


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue or revoke a scoped API key.")
    parser.add_argument("--email", help="Account this key may touch")
    parser.add_argument("--label", help="Name for the row, for example local-load-test")
    parser.add_argument("--scopes", help="Comma-separated: data, llm, or both")
    parser.add_argument("--revoke", type=int, metavar="ID", help="Revoke this credential id")
    args = parser.parse_args(argv)

    create_tables()
    if args.revoke is not None:
        revoke_api_credential(args.revoke)
        print(f"revoked credential_id={args.revoke}")
        return 0

    if not args.email or not args.label or not args.scopes:
        parser.error("--email, --label, and --scopes are required to issue a key")
    account = get_account_by_email(args.email)
    if account is None:
        print("No account with that email.", file=sys.stderr)
        return 1
    try:
        raw_key, credential_id = issue_api_credential(
            account["id"],
            args.label,
            [part.strip() for part in args.scopes.split(",")],
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"credential_id={credential_id}")
    print(raw_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
