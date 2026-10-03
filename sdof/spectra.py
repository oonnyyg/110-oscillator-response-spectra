"""Response spectra computation and CSV/JSON export."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

from .newmark import ResponseHistory, compute_response


@dataclass(frozen=True)
class SpectrumResult:
    period: float
    damping_ratio: float
    peak_relative_displacement: float
    peak_relative_velocity: float
    peak_absolute_acceleration: float
    pseudo_acceleration: float


def compute_spectra(
    time: list[float],
    acceleration: list[float],
    periods: list[float],
    damping_ratio: float,
) -> tuple[list[ResponseHistory], list[SpectrumResult]]:
    """Run one Newmark integration per period and collect peak statistics."""
    histories: list[ResponseHistory] = []
    results: list[SpectrumResult] = []
    for period in periods:
        history = compute_response(time, acceleration, period, damping_ratio)
        histories.append(history)
        omega = 2.0 * math.pi / period
        results.append(
            SpectrumResult(
                period=period,
                damping_ratio=damping_ratio,
                peak_relative_displacement=history.peak_displacement,
                peak_relative_velocity=history.peak_velocity,
                peak_absolute_acceleration=history.peak_absolute_acceleration,
                pseudo_acceleration=omega * omega * history.peak_displacement,
            )
        )
    return histories, results


def write_history_csv(path: str | Path, history: ResponseHistory) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "time_s",
                "relative_displacement_m",
                "relative_velocity_m_per_s",
                "absolute_acceleration_m_per_s2",
            ]
        )
        for index in range(len(history.time)):
            writer.writerow(
                [
                    history.time[index],
                    history.relative_displacement[index],
                    history.relative_velocity[index],
                    history.absolute_acceleration[index],
                ]
            )


def write_spectra_json(
    path: str | Path, results: list[SpectrumResult]
) -> None:
    payload = [
        {
            "period_s": result.period,
            "damping_ratio": result.damping_ratio,
            "peak_relative_displacement_m": result.peak_relative_displacement,
            "peak_relative_velocity_m_per_s": result.peak_relative_velocity,
            "peak_absolute_acceleration_m_per_s2": (
                result.peak_absolute_acceleration
            ),
            "pseudo_acceleration_m_per_s2": result.pseudo_acceleration,
        }
        for result in results
    ]
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
