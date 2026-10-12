"""Command-line parsing; stdout is JSON and diagnostics go to stderr."""
import argparse
import json
from pathlib import Path
import sys

from .compiler import parse_document
from .model import InvalidSource, to_data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate DocSource and emit format-independent SemanticIR")
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse", help="Load, parse and validate a body-only document")
    parse.add_argument("source", type=Path, help="DocSource directory or document.yaml")
    parse.add_argument("--profile", type=Path, help="Profile YAML for structural schema validation")
    parse.add_argument("--output", "-o", type=Path, help="Write JSON to a new file (default: stdout)")
    build = commands.add_parser("build", help="Generate a Word document and conformance report")
    build.add_argument("source", type=Path)
    build.add_argument("--profile", type=Path, required=True)
    build.add_argument("--output", "-o", type=Path, required=True, help="Directory for build artifacts (replaced if it already exists)")
    build.add_argument("--refresh", action="store_true", help="Evaluate LibreOffice field refresh, keeping original if checks fail")
    build.add_argument("--pdf", action="store_true", help="Also render a PDF preview with LibreOffice")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            from .build import build_document
            report = build_document(args.source, args.profile, args.output, refresh=args.refresh, pdf=args.pdf)
            print(json.dumps({"output": str(args.output), "counts": report["counts"], "findings": report["findings"]}, ensure_ascii=False, indent=2))
            return 0
        result = parse_document(args.source, args.profile)
        payload = json.dumps(to_data(result), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Do not overwrite source or an earlier result by accident.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        else:
            sys.stdout.write(payload)
        for finding in result.diagnostics:
            print(f"{finding.source.file}:{finding.source.line}: {finding.severity} [{finding.code}] {finding.message}", file=sys.stderr)
        return 0
    except InvalidSource as exc:
        print(json.dumps({"diagnostics": to_data(exc.diagnostics)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
