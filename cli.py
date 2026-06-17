"""
Command-line interface for the Intelligent File Organizer.
"""

import argparse
import json
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))
from organizer import FileOrganizer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-organizer",
        description="🗂  Intelligent File Organizer — sort files by type automatically.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --source ~/Downloads
  python cli.py --source ~/Downloads --output ~/Organized --dry-run
  python cli.py --source ~/Desktop --report report.json
        """,
    )

    parser.add_argument(
        "--source", "-s",
        required=True,
        help="Directory to organize.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: same as source).",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview changes without moving any files.",
    )
    parser.add_argument(
        "--no-duplicates",
        action="store_true",
        help="Skip duplicate detection (faster for large directories).",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help="Directory to write log files (default: console only).",
    )
    parser.add_argument(
        "--report", "-r",
        default=None,
        metavar="FILE",
        help="Save a JSON report to this path.",
    )

    return parser


def main():
    args = build_parser().parse_args()

    try:
        organizer = FileOrganizer(
            source_dir        = args.source,
            output_dir        = args.output,
            handle_duplicates = not args.no_duplicates,
            dry_run           = args.dry_run,
            log_dir           = args.log_dir,
        )

        report = organizer.organize()

        if args.report:
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n Report saved to: {args.report}")

        # Exit code reflects errors
        sys.exit(1 if report["stats"]["errors"] else 0)

    except NotADirectoryError as e:
        print(f"\n {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n  Interrupted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
