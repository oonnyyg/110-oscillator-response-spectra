"""Response spectra computation and CSV/JSON export."""

from __future__ import annotations

import csv
import json
import math

from sdof import Response, solve_sdof, validate_damping, validate_time_series


def compute_spectrum(
    times: list[float],
    ground_accels: list[float],
    periods: list[float],
    damping: float,
) -> list[dict]:
    """Compute response spectra for each period.

    Returns one entry per period with peak relative displacement (Sd),
    peak relative velocity (Sv), peak absolute acceleration (Sa_abs) and
    pseudo-acceleration Psa = omega^2 * Sd.
    """
    validate_time_series(times, ground_accels)
    validate_damping(damping)
    results = []
    for period in periods:
        resp = solve_sdof(times, ground_accels, period, damping)
        omega = 2.0 * math.pi / period
        sd = resp.peak_displacement()
        results.append(
            {
                "period": period,
                "omega": omega,
                "peak_displacement": sd,
                "peak_velocity": resp.peak_velocity(),
                "peak_abs_acceleration": resp.peak_abs_acceleration(),
                "pseudo_acceleration": omega * omega * sd,
            }
        )
    return results


def export_history_csv(response: Response, path: str) -> None:
    """Write time history: time, rel displacement, rel velocity, abs accel."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["time_s", "rel_displacement_m", "rel_velocity_mps",
             "abs_acceleration_mps2"]
        )
        for i, t in enumerate(response.times):
            writer.writerow(
                [t, response.displacement[i], response.velocity[i],
                 response.abs_acceleration[i]]
            )


def export_spectrum_json(spectrum: list[dict], damping: float, path: str) -> None:
    payload = {
        "damping_ratio": damping,
        "units": {
            "period": "s",
            "peak_displacement": "m",
            "peak_velocity": "m/s",
            "peak_abs_acceleration": "m/s^2",
            "pseudo_acceleration": "m/s^2",
        },
        "spectra": spectrum,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
