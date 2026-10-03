"""Loading and validation of JSON time series and run configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class InputError(ValueError):
    """Raised when an input file fails validation."""


@dataclass(frozen=True)
class TimeSeries:
    time: list[float]
    acceleration: list[float]


@dataclass(frozen=True)
class Config:
    periods: list[float]
    damping_ratio: float


def _load_json(path: str | Path) -> object:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise InputError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc


def _as_number_list(value: object, name: str) -> list[float]:
    if not isinstance(value, list):
        raise InputError(f"'{name}' must be a JSON array of numbers")
    result: list[float] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise InputError(f"'{name}[{index}]' is not a number: {item!r}")
        result.append(float(item))
    return result


def load_time_series(path: str | Path) -> TimeSeries:
    data = _load_json(path)
    if not isinstance(data, dict):
        raise InputError(f"time series file {path} must contain a JSON object")
    if "time" not in data or "acceleration" not in data:
        raise InputError("time series must define 'time' and 'acceleration' arrays")
    time = _as_number_list(data["time"], "time")
    acceleration = _as_number_list(data["acceleration"], "acceleration")
    if len(time) != len(acceleration):
        raise InputError(
            f"'time' ({len(time)}) and 'acceleration' ({len(acceleration)}) "
            "must have the same length"
        )
    if len(time) < 2:
        raise InputError("time series must contain at least two points")
    for index in range(1, len(time)):
        if not time[index] > time[index - 1]:
            raise InputError(
                f"time must be strictly increasing: "
                f"time[{index - 1}]={time[index - 1]} >= time[{index}]={time[index]}"
            )
    return TimeSeries(time=time, acceleration=acceleration)


def load_config(path: str | Path) -> Config:
    data = _load_json(path)
    if not isinstance(data, dict):
        raise InputError(f"config file {path} must contain a JSON object")
    if "periods" not in data or "damping_ratio" not in data:
        raise InputError("config must define 'periods' and 'damping_ratio'")
    periods = _as_number_list(data["periods"], "periods")
    if not periods:
        raise InputError("'periods' must not be empty")
    for period in periods:
        if period <= 0.0:
            raise InputError(f"periods must be positive, got {period}")
    damping = data["damping_ratio"]
    if isinstance(damping, bool) or not isinstance(damping, (int, float)):
        raise InputError(f"'damping_ratio' must be a number, got {damping!r}")
    damping = float(damping)
    if not 0.0 <= damping < 1.0:
        raise InputError(
            f"damping ratio must satisfy 0 <= damping_ratio < 1, got {damping}"
        )
    return Config(periods=periods, damping_ratio=damping)
