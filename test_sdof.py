"""Tests for SDOF response: zero input, single-step recursion, variable dt."""

from __future__ import annotations

import math
import unittest

from sdof import BETA, GAMMA, InputError, solve_sdof
from spectra import compute_spectrum


class TestZeroInput(unittest.TestCase):
    def test_zero_ground_motion_gives_zero_response(self):
        times = [0.0, 0.1, 0.25, 0.4]
        accels = [0.0] * len(times)
        resp = solve_sdof(times, accels, period=1.0, damping=0.05)
        for series in (resp.displacement, resp.velocity, resp.abs_acceleration):
            for value in series:
                self.assertEqual(value, 0.0)
        self.assertEqual(resp.peak_displacement(), 0.0)
        self.assertEqual(resp.peak_abs_acceleration(), 0.0)


class TestSingleStep(unittest.TestCase):
    def test_one_step_matches_hand_computed_newmark(self):
        period, damping = 0.8, 0.05
        omega = 2.0 * math.pi / period
        k = omega * omega
        c = 2.0 * damping * omega
        dt = 0.02
        g0, g1 = 0.3, 0.5

        resp = solve_sdof([0.0, dt], [g0, g1], period, damping)

        # Initial acceleration from the equation of motion.
        a0 = -g0
        self.assertAlmostEqual(resp.displacement[0], 0.0)
        self.assertAlmostEqual(resp.velocity[0], 0.0)
        self.assertAlmostEqual(resp.abs_acceleration[0], a0 + g0)

        # Hand-computed Newmark average-acceleration step.
        u_pred = dt * dt * (0.5 - BETA) * a0
        v_pred = dt * (1.0 - GAMMA) * a0
        denom = 1.0 + GAMMA * dt * c + BETA * dt * dt * k
        a1 = (-g1 - c * v_pred - k * u_pred) / denom
        v1 = v_pred + dt * GAMMA * a1
        u1 = u_pred + dt * dt * BETA * a1

        self.assertAlmostEqual(resp.displacement[1], u1)
        self.assertAlmostEqual(resp.velocity[1], v1)
        self.assertAlmostEqual(resp.abs_acceleration[1], a1 + g1)


class TestVariableStep(unittest.TestCase):
    def test_variable_dt_matches_fine_reference(self):
        # Irregular sampling of the same smooth ground motion must give
        # nearly the same response as a fine, equally spaced record.
        period, damping = 0.5, 0.02

        def ground(t: float) -> float:
            return 0.4 * math.sin(3.0 * t) + 0.2 * math.sin(11.0 * t)

        fine_times = [i * 0.001 for i in range(2001)]
        fine = solve_sdof(fine_times, [ground(t) for t in fine_times],
                          period, damping)

        coarse_times = []
        t = 0.0
        while t < 2.0 - 1e-12:
            coarse_times.append(t)
            t += 0.004 if int(t * 1000) % 3 else 0.0015
        coarse_times.append(2.0)
        coarse = solve_sdof(coarse_times, [ground(t) for t in coarse_times],
                            period, damping)

        self.assertAlmostEqual(
            coarse.displacement[-1], fine.displacement[-1], delta=1e-4
        )
        self.assertAlmostEqual(
            coarse.velocity[-1], fine.velocity[-1], delta=1e-3
        )

    def test_variable_dt_not_treated_as_uniform(self):
        # An irregular record must differ from the same samples wrongly
        # integrated on a uniform grid.
        times = [0.0, 0.01, 0.05, 0.051, 0.2]
        accels = [0.0, 1.0, -0.5, 0.8, 0.1]
        period, damping = 1.0, 0.05
        irregular = solve_sdof(times, accels, period, damping)
        uniform = solve_sdof([0.0, 0.05, 0.1, 0.15, 0.2], accels,
                             period, damping)
        self.assertNotAlmostEqual(
            irregular.displacement[-1], uniform.displacement[-1], places=6
        )


class TestValidation(unittest.TestCase):
    def test_rejects_short_series(self):
        with self.assertRaises(InputError):
            solve_sdof([0.0], [0.0], 1.0, 0.05)

    def test_rejects_non_increasing_time(self):
        with self.assertRaises(InputError):
            solve_sdof([0.0, 0.1, 0.1], [0.0, 0.0, 0.0], 1.0, 0.05)
        with self.assertRaises(InputError):
            solve_sdof([0.0, 0.1, 0.05], [0.0, 0.0, 0.0], 1.0, 0.05)

    def test_rejects_bad_period_and_damping(self):
        times, accels = [0.0, 0.1], [0.0, 0.0]
        for bad_period in (0.0, -1.0):
            with self.assertRaises(InputError):
                solve_sdof(times, accels, bad_period, 0.05)
        for bad_damping in (0.0, 1.0, 1.5, -0.1):
            with self.assertRaises(InputError):
                solve_sdof(times, accels, 1.0, bad_damping)

    def test_rejects_length_mismatch(self):
        with self.assertRaises(InputError):
            solve_sdof([0.0, 0.1], [0.0], 1.0, 0.05)


class TestSpectrum(unittest.TestCase):
    def test_pseudo_acceleration_is_omega_squared_times_sd(self):
        times = [i * 0.01 for i in range(500)]
        accels = [math.sin(2.0 * t) for t in times]
        spectrum = compute_spectrum(times, accels, [0.2, 1.0], 0.05)
        self.assertEqual(len(spectrum), 2)
        for entry in spectrum:
            omega = 2.0 * math.pi / entry["period"]
            self.assertAlmostEqual(entry["omega"], omega)
            self.assertAlmostEqual(
                entry["pseudo_acceleration"],
                omega * omega * entry["peak_displacement"],
            )
            self.assertGreaterEqual(entry["peak_abs_acceleration"], 0.0)


if __name__ == "__main__":
    unittest.main()
