"""Command line entry point for SDOF response and response spectra.

Usage:
    python main.py CONFIG.json

Config JSON:
    {
      "record_file": "record.json",        // JSON with "time" and "acceleration"
      "periods": [0.1, 0.5, 1.0, 2.0],     // seconds, all > 0
      "damping": 0.05,                     // ratio, 0 < zeta < 1
      "output_dir": "out"                  // optional, default "."
    }

Record JSON:
    {"time": [0.0, 0.01, ...], "acceleration": [0.0, 0.2, ...]}
    time in seconds (strictly increasing, >= 2 points, may be unequally
    spaced), acceleration in m/s^2.

Outputs per period a CSV time history (history_T<period>s.csv) and a
JSON spectrum table (spectra.json) in the output directory.
"""

from __future__ import annotations

import json
import sys

from sdof import InputError, solve_sdof
from spectra import compute_spectrum, export_history_csv, export_spectrum_json


def _load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc


def _load_record(config: dict, config_dir: str) -> tuple[list, list]:
    import os

    record = config.get("record")
    if record is None:
        record_file = config.get("record_file")
        if not record_file:
            raise InputError("config must contain 'record' or 'record_file'")
        record = _load_json(os.path.join(config_dir, record_file))
    try:
        times = [float(x) for x in record["time"]]
        accels = [float(x) for x in record["acceleration"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise InputError(
            "record must contain numeric 'time' and 'acceleration' arrays"
        ) from exc
    return times, accels


def _load_config(path: str) -> dict:
    import os

    config = _load_json(path)
    times, accels = _load_record(config, os.path.dirname(os.path.abspath(path)))
    try:
        periods = [float(p) for p in config["periods"]]
        damping = float(config["damping"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InputError(
            "config must contain numeric 'periods' array and 'damping'"
        ) from exc
    if not periods:
        raise InputError("config 'periods' must not be empty")
    output_dir = config.get("output_dir", ".")
    return {
        "times": times,
        "accels": accels,
        "periods": periods,
        "damping": damping,
        "output_dir": output_dir,
    }


def run(config_path: str) -> None:
    import os

    cfg = _load_config(config_path)
    os.makedirs(cfg["output_dir"], exist_ok=True)

    spectrum = compute_spectrum(
        cfg["times"], cfg["accels"], cfg["periods"], cfg["damping"]
    )
    for period in cfg["periods"]:
        resp = solve_sdof(cfg["times"], cfg["accels"], period, cfg["damping"])
        csv_path = os.path.join(cfg["output_dir"], f"history_T{period:g}s.csv")
        export_history_csv(resp, csv_path)
        print(f"wrote {csv_path}")

    json_path = os.path.join(cfg["output_dir"], "spectra.json")
    export_spectrum_json(spectrum, cfg["damping"], json_path)
    print(f"wrote {json_path}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        run(argv[1])
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
