"""Command line entry point for SDOF response and spectra computation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .io import InputError, load_config, load_time_series
from .spectra import compute_spectra, write_history_csv, write_spectra_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdof-spectra",
        description=(
            "Compute SDOF oscillator response histories and response spectra "
            "from a ground acceleration record (JSON, seconds and m/s^2)."
        ),
    )
    parser.add_argument("record", help="JSON time series file")
    parser.add_argument("config", help="JSON configuration file")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="directory for CSV histories and spectra.json (default: output)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        series = load_time_series(args.record)
        config = load_config(args.config)
    except InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2

    histories, results = compute_spectra(
        series.time, series.acceleration, config.periods, config.damping_ratio
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for period, history in zip(config.periods, histories):
        write_history_csv(output_dir / f"history_T{period:g}s.csv", history)
    spectra_path = output_dir / "spectra.json"
    write_spectra_json(spectra_path, results)

    print(f"wrote {len(histories)} history CSV file(s) and {spectra_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
