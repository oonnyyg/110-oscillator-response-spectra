"""Newmark average-acceleration integration of the SDOF equation of motion.

Solves, for a unit-mass oscillator,

    u'' + 2*zeta*omega*u' + omega^2*u = -ag(t)

where u is the relative displacement, omega the circular frequency, zeta the
damping ratio and ag the ground acceleration. Absolute acceleration is
u'' + ag.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

GAMMA = 0.5  # velocity update coefficient (average acceleration)
BETA = 0.25  # displacement update coefficient (average acceleration)


@dataclass(frozen=True)
class ResponseHistory:
    time: list[float]
    relative_displacement: list[float]
    relative_velocity: list[float]
    absolute_acceleration: list[float]

    @property
    def peak_displacement(self) -> float:
        return max(abs(value) for value in self.relative_displacement)

    @property
    def peak_velocity(self) -> float:
        return max(abs(value) for value in self.relative_velocity)

    @property
    def peak_absolute_acceleration(self) -> float:
        return max(abs(value) for value in self.absolute_acceleration)


def compute_response(
    time: list[float],
    acceleration: list[float],
    period: float,
    damping_ratio: float,
) -> ResponseHistory:
    """Integrate one oscillator over the record using per-step time increments."""
    if len(time) != len(acceleration):
        raise ValueError("time and acceleration must have the same length")
    if len(time) < 2:
        raise ValueError("at least two time points are required")
    if period <= 0.0:
        raise ValueError(f"period must be positive, got {period}")
    if not 0.0 <= damping_ratio < 1.0:
        raise ValueError(f"damping ratio must be in [0, 1), got {damping_ratio}")

    omega = 2.0 * math.pi / period
    stiffness = omega * omega
    damping = 2.0 * damping_ratio * omega

    count = len(time)
    displacement = [0.0] * count
    velocity = [0.0] * count
    rel_accel = [0.0] * count

    # Initial relative displacement and velocity are zero, so the equation of
    # motion at t[0] gives the initial relative acceleration directly.
    rel_accel[0] = -acceleration[0]

    for index in range(1, count):
        dt = time[index] - time[index - 1]
        if dt <= 0.0:
            raise ValueError(
                f"time must be strictly increasing at index {index}: "
                f"{time[index - 1]} -> {time[index]}"
            )
        u_pred = (
            displacement[index - 1]
            + dt * velocity[index - 1]
            + dt * dt * (0.5 - BETA) * rel_accel[index - 1]
        )
        v_pred = velocity[index - 1] + dt * (1.0 - GAMMA) * rel_accel[index - 1]
        denominator = 1.0 + GAMMA * dt * damping + BETA * dt * dt * stiffness
        rel_accel[index] = (
            -acceleration[index] - damping * v_pred - stiffness * u_pred
        ) / denominator
        velocity[index] = v_pred + GAMMA * dt * rel_accel[index]
        displacement[index] = u_pred + BETA * dt * dt * rel_accel[index]

    absolute = [rel_accel[i] + acceleration[i] for i in range(count)]
    return ResponseHistory(
        time=list(time),
        relative_displacement=displacement,
        relative_velocity=velocity,
        absolute_acceleration=absolute,
    )
