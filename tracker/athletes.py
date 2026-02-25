from __future__ import annotations

import argparse

from tracker.config import AppConfig
from tracker.db import Database


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tracker.athletes")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add")
    add.add_argument("name")
    add.add_argument("--club", default=None)

    remove = sub.add_parser("remove")
    remove.add_argument("name")

    sub.add_parser("list")

    args = parser.parse_args(argv)
    config = AppConfig.load()
    db = Database(config.db_path)
    db.init_schema()
    try:
        if args.command == "add":
            db.add_athlete(args.name, args.club)
            print(f"saved athlete: {args.name}")
            return 0
        if args.command == "remove":
            count = db.remove_athlete(args.name)
            print(f"removed: {count}")
            return 0
        if args.command == "list":
            athletes = db.list_athletes()
            if not athletes:
                print("no athletes configured")
                return 0
            for athlete in athletes:
                club = athlete.club or "-"
                print(f"{athlete.display_name}\tclub={club}")
            return 0
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
