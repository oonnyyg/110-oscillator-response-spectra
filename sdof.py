"""SDOF oscillator response via Newmark average acceleration.

Units: time in seconds, ground acceleration in m/s^2, displacement in m,
velocity in m/s, acceleration in m/s^2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

GAMMA = 0.5  # Newmark velocity coefficient (average acceleration)
BETA = 0.25  # Newmark displacement coefficient (average acceleration)


class InputError(ValueError):
    """Raised when the time series or configuration is invalid."""


@dataclass
class Response:
    times: list[float]
    displacement: list[float]  # relative displacement, m
    velocity: list[float]  # relative velocity, m/s
    abs_acceleration: list[float]  # absolute acceleration, m/s^2

    def peak_displacement(self) -> float:
        return max(abs(v) for v in self.displacement)

    def peak_velocity(self) -> float:
        return max(abs(v) for v in self.velocity)

    def peak_abs_acceleration(self) -> float:
        return max(abs(v) for v in self.abs_acceleration)


def validate_time_series(times: list[float], accels: list[float]) -> None:
    if len(times) != len(accels):
        raise InputError(
            f"time and acceleration lengths differ: {len(times)} vs {len(accels)}"
        )
    if len(times) < 2:
        raise InputError("time series must contain at least two points")
    for i in range(1, len(times)):
        if not times[i] > times[i - 1]:
            raise InputError(
                f"time must be strictly increasing: t[{i - 1}]={times[i - 1]}, "
                f"t[{i}]={times[i]}"
            )


def validate_period(period: float) -> None:
    if not period > 0.0:
        raise InputError(f"period must be positive, got {period}")


def validate_damping(damping: float) -> None:
    if not 0.0 < damping < 1.0:
        raise InputError(
            f"damping ratio must be between 0 and 1 (exclusive), got {damping}"
        )


def solve_sdof(
    times: list[float],
    ground_accels: list[float],
    period: float,
    damping: float,
) -> Response:
    """Solve u'' + 2*zeta*omega*u' + omega^2*u = -ag (unit mass).

    Newmark average acceleration (gamma=1/2, beta=1/4) using the actual
    time step of each interval, so unequally spaced records are handled
    correctly. Peaks are taken over discrete time points only.
    """
    validate_time_series(times, ground_accels)
    validate_period(period)
    validate_damping(damping)

    omega = 2.0 * math.pi / period
    k = omega * omega
    c = 2.0 * damping * omega

    n = len(times)
    u = [0.0] * n  # relative displacement
    v = [0.0] * n  # relative velocity
    a = [0.0] * n  # relative acceleration

    # Initial relative acceleration from the equation of motion at t0.
    a[0] = -ground_accels[0] - c * v[0] - k * u[0]

    for i in range(1, n):
        dt = times[i] - times[i - 1]
        u_pred = u[i - 1] + dt * v[i - 1] + dt * dt * (0.5 - BETA) * a[i - 1]
        v_pred = v[i - 1] + dt * (1.0 - GAMMA) * a[i - 1]
        denom = 1.0 + GAMMA * dt * c + BETA * dt * dt * k
        a[i] = (-ground_accels[i] - c * v_pred - k * u_pred) / denom
        v[i] = v_pred + dt * GAMMA * a[i]
        u[i] = u_pred + dt * dt * BETA * a[i]

    abs_accel = [a[i] + ground_accels[i] for i in range(n)]
    return Response(
        times=list(times),
        displacement=u,
        velocity=v,
        abs_acceleration=abs_accel,
    )
