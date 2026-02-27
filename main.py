"""
Mini Data Proxy — reference implementation of proxy re-encryption
for multi-party data sharing using PyUmbral.

Run with --help to see available commands and options.
"""

import argparse
import sys

from umbral import SecretKey, Signer
from src.database import store_data, consume_data
from src.config import PRE_THRESHOLD, PRE_SHARES
from src.logger import get_logger

log = get_logger("mini-data-proxy")


def demo(args: argparse.Namespace) -> None:
    """Run the full encrypt → store → consume round-trip."""

    database: dict = {"collection": {}}

    # ── Key generation ──────────────────────────────────────────
    owner_sk = SecretKey.random()
    owner_pk = owner_sk.public_key()
    owner_signer = Signer(owner_sk)

    consumer_sk = SecretKey.random()
    consumer_pk = consumer_sk.public_key()

    # ── Data preparation ────────────────────────────────────────
    asset_id = args.asset_id
    payload = args.data.encode() if isinstance(args.data, str) else args.data
    access_url = args.access_url

    log.info("Running end-to-end PRE demo for asset '%s'", asset_id)

    # ── Store (handles encryption + kfrag generation internally) ─
    store_data(
        database, asset_id, payload, access_url,
        owner_sk, owner_signer, consumer_pk,
    )

    # ── Consume ─────────────────────────────────────────────────
    try:
        decrypted, link = consume_data(
            database, asset_id, "consumer_address",
            consumer_sk, owner_pk, consumer_pk,
        )
        print(f"Decrypted : {decrypted}")
        print(f"Access URL: {link}")
    except (ValueError, PermissionError) as exc:
        log.error("Consumption failed: %s", exc)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mini-data-proxy",
        description="Proxy Re-Encryption data sharing demo",
    )
    sub = parser.add_subparsers(dest="command")

    # ── demo sub-command ────────────────────────────────────────
    p_demo = sub.add_parser("demo", help="Run the full PRE round-trip")
    p_demo.add_argument(
        "--data", default="Sample data",
        help="Plaintext payload to encrypt (default: 'Sample data')",
    )
    p_demo.add_argument(
        "--asset-id", default="asset-001",
        help="Unique data-asset identifier (default: asset-001)",
    )
    p_demo.add_argument(
        "--access-url", default="https://example.com/data",
        help="URL stored in the DID document",
    )
    p_demo.add_argument(
        "--threshold", type=int, default=PRE_THRESHOLD,
        help=f"Minimum kfrags for decryption (default: {PRE_THRESHOLD})",
    )
    p_demo.add_argument(
        "--shares", type=int, default=PRE_SHARES,
        help=f"Total kfrags to generate (default: {PRE_SHARES})",
    )
    p_demo.set_defaults(func=demo)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
