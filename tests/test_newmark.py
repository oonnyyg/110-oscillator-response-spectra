import math
import unittest

from sdof.newmark import BETA, GAMMA, compute_response


class ZeroInputTest(unittest.TestCase):
    def test_zero_ground_motion_gives_zero_response(self):
        time = [0.0, 0.1, 0.25, 0.4]
        acceleration = [0.0] * len(time)
        history = compute_response(time, acceleration, period=0.5, damping_ratio=0.05)
        for values in (
            history.relative_displacement,
            history.relative_velocity,
            history.absolute_acceleration,
        ):
            self.assertTrue(all(value == 0.0 for value in values))
        self.assertEqual(history.peak_displacement, 0.0)
        self.assertEqual(history.peak_absolute_acceleration, 0.0)


class SingleStepTest(unittest.TestCase):
    def test_first_step_matches_hand_computed_newmark(self):
        time = [0.0, 0.1]
        acceleration = [1.0, 2.0]
        period = 0.4
        zeta = 0.05
        omega = 2.0 * math.pi / period
        k = omega * omega
        c = 2.0 * zeta * omega
        dt = 0.1
        a0 = -1.0
        u_pred = dt * dt * (0.5 - BETA) * a0
        v_pred = dt * (1.0 - GAMMA) * a0
        denom = 1.0 + GAMMA * dt * c + BETA * dt * dt * k
        a1 = (-2.0 - c * v_pred - k * u_pred) / denom
        v1 = v_pred + GAMMA * dt * a1
        u1 = u_pred + BETA * dt * dt * a1
        history = compute_response(time, acceleration, period, zeta)
        self.assertAlmostEqual(history.relative_displacement[0], 0.0)
        self.assertAlmostEqual(history.relative_velocity[0], 0.0)
        self.assertAlmostEqual(history.absolute_acceleration[0], 0.0)
        self.assertAlmostEqual(history.relative_displacement[1], u1)
        self.assertAlmostEqual(history.relative_velocity[1], v1)
        self.assertAlmostEqual(history.absolute_acceleration[1], a1 + 2.0)


class VariableStepTest(unittest.TestCase):
    def _reference_integrate(self, time, acceleration, period, zeta):
        omega = 2.0 * math.pi / period
        k = omega * omega
        c = 2.0 * zeta * omega
        u, v = 0.0, 0.0
        a = -acceleration[0]
        out = [(u, v, a + acceleration[0])]
        for i in range(1, len(time)):
            dt = time[i] - time[i - 1]
            u_pred = u + dt * v + dt * dt * (0.5 - BETA) * a
            v_pred = v + dt * (1.0 - GAMMA) * a
            a = (-acceleration[i] - c * v_pred - k * u_pred) / (
                1.0 + GAMMA * dt * c + BETA * dt * dt * k
            )
            v = v_pred + GAMMA * dt * a
            u = u_pred + BETA * dt * dt * a
            out.append((u, v, a + acceleration[i]))
        return out

    def test_irregular_grid_uses_actual_time_steps(self):
        time = [0.0, 0.03, 0.11, 0.2, 0.31, 0.5]
        acceleration = [0.0, 0.5, -1.0, 0.8, -0.3, 0.1]
        period, zeta = 0.3, 0.02
        history = compute_response(time, acceleration, period, zeta)
        reference = self._reference_integrate(time, acceleration, period, zeta)
        for i, (u, v, a_abs) in enumerate(reference):
            self.assertAlmostEqual(history.relative_displacement[i], u)
            self.assertAlmostEqual(history.relative_velocity[i], v)
            self.assertAlmostEqual(history.absolute_acceleration[i], a_abs)

    def test_irregular_grid_differs_from_uniform_assumption(self):
        time = [0.0, 0.02, 0.15, 0.2]
        acceleration = [0.0, 1.0, -0.5, 0.25]
        period, zeta = 0.5, 0.05
        irregular = compute_response(time, acceleration, period, zeta)
        uniform = compute_response(
            [0.0, 0.05, 0.10, 0.15], acceleration, period, zeta
        )
        self.assertNotAlmostEqual(
            irregular.relative_displacement[-1], uniform.relative_displacement[-1]
        )

    def test_converges_to_analytic_constant_acceleration_solution(self):
        # Undamped oscillator under constant ground acceleration ag:
        # u(t) = -(ag/omega^2) * (1 - cos(omega*t)).
        period, zeta, ag = 1.0, 0.0, 1.0
        omega = 2.0 * math.pi / period
        duration = 0.7
        steps = 20000
        time = [duration * i / steps for i in range(steps + 1)]
        acceleration = [ag] * len(time)
        history = compute_response(time, acceleration, period, zeta)
        expected = -(ag / (omega * omega)) * (1.0 - math.cos(omega * duration))
        self.assertAlmostEqual(
            history.relative_displacement[-1], expected, places=6
        )


if __name__ == "__main__":
    unittest.main()
