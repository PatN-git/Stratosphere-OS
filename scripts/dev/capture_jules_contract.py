#!/usr/bin/env python3
"""Capture REAL Jules v1alpha responses to verify/refresh the pinned contract (P0/P7).

Read-only by default (GET /sources, GET /sessions/{id}). Reads JULES_API_KEY from
.env.local. Run this during the live E2E to confirm CONTRACT.md against the real API
and, with --write, refresh the hand-authored fixtures.

  python scripts/dev/capture_jules_contract.py --smoke            # GET /sources, print count
  python scripts/dev/capture_jules_contract.py --session <id>     # dump a real Session resource
  python scripts/dev/capture_jules_contract.py --smoke --write    # also write *.live.json fixtures
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "experimental" / "jules-dispatch"))
from config import load_api_key       # noqa: E402
from jules_api import JulesClient, JulesError  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "jules"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Capture real Jules API responses (read-only).")
    ap.add_argument("--smoke", action="store_true", help="GET /sources and print the count")
    ap.add_argument("--session", help="GET a session by id and print it")
    ap.add_argument("--write", action="store_true", help="also write captured JSON as *.live.json fixtures")
    args = ap.parse_args(argv)

    try:
        client = JulesClient(api_key=load_api_key(project_root=str(ROOT)))
    except JulesError as e:
        print(f"config error: {e}")
        return 2

    if args.smoke or not args.session:
        srcs = client.list_sources()
        print(f"sources: {len(srcs)}")
        for s in srcs[:10]:
            print("  -", s.get("id") or s.get("name"))
        if args.write:
            FIX.mkdir(parents=True, exist_ok=True)
            (FIX / "sources.live.json").write_text(json.dumps({"sources": srcs}, indent=2), encoding="utf-8")
            print(f"wrote {FIX / 'sources.live.json'}")

    if args.session:
        sess = client.get_session(args.session)
        print(json.dumps(sess, indent=2))
        if args.write:
            FIX.mkdir(parents=True, exist_ok=True)
            (FIX / "session.live.json").write_text(json.dumps(sess, indent=2), encoding="utf-8")
            print(f"wrote {FIX / 'session.live.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
