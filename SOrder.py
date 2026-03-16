"""
CLI entrypoint for shared library dependency analysis.
"""

import argparse
import os
import sys
from os.path import join, normpath

from dependency_analyzer import analyze_dependencies
from html_report import render_html_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze shared library dependencies and render an HTML report."
    )
    parser.add_argument(
        "--root",
        action="append",
        required=True,
        help="Root directory to scan (repeatable).",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only scan the root directory, not subdirectories.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (HTML). Defaults to <common-root>/so_dependencies.html.",
    )
    parser.add_argument(
        "--focus",
        default=None,
        help="Initially selected library. Accepts basename, SONAME, or relative path.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    roots = [normpath(root) for root in args.root]

    missing = [root for root in roots if not os.path.isdir(root)]
    if missing:
        print(f"Directory not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    base_dir = os.path.commonpath(roots) if len(roots) > 1 else roots[0]
    output_path = args.output or join(base_dir, "so_dependencies.html")

    report_data = analyze_dependencies(roots, recursive=not args.no_recursive)
    if report_data is None:
        print("No shared libraries found under:", ", ".join(roots))
        return 0

    output_html = render_html_report(report_data, initial_focus=args.focus)

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(output_html)
    except OSError as exc:
        print(f"ERROR writing output file: {exc}", file=sys.stderr)
        return 2

    print(
        f"Wrote HTML dependency report for {len(report_data['libraries'])} files to: {output_path}"
    )
    if report_data["cycles"]:
        print("Cycle detected; the HTML report marks cyclic paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
