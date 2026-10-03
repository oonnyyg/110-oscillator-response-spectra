import json
import tempfile
import unittest
from pathlib import Path

from sdof.io import InputError, load_config, load_time_series


def _write(directory, name, payload):
    path = Path(directory) / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TimeSeriesValidationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_valid_series_loads(self):
        path = _write(
            self.dir, "ok.json", {"time": [0.0, 0.1, 0.3], "acceleration": [0, 1, 2]}
        )
        series = load_time_series(path)
        self.assertEqual(series.time, [0.0, 0.1, 0.3])
        self.assertEqual(series.acceleration, [0.0, 1.0, 2.0])

    def test_non_increasing_time_rejected(self):
        path = _write(
            self.dir, "bad.json", {"time": [0.0, 0.1, 0.1], "acceleration": [0, 1, 2]}
        )
        with self.assertRaisesRegex(InputError, "strictly increasing"):
            load_time_series(path)

    def test_too_few_points_rejected(self):
        path = _write(self.dir, "short.json", {"time": [0.0], "acceleration": [0.0]})
        with self.assertRaisesRegex(InputError, "at least two"):
            load_time_series(path)

    def test_length_mismatch_rejected(self):
        path = _write(
            self.dir, "mismatch.json", {"time": [0.0, 0.1], "acceleration": [0.0]}
        )
        with self.assertRaisesRegex(InputError, "same length"):
            load_time_series(path)


class ConfigValidationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_valid_config_loads(self):
        path = _write(
            self.dir, "cfg.json", {"periods": [0.1, 0.5], "damping_ratio": 0.05}
        )
        config = load_config(path)
        self.assertEqual(config.periods, [0.1, 0.5])
        self.assertAlmostEqual(config.damping_ratio, 0.05)

    def test_non_positive_period_rejected(self):
        path = _write(self.dir, "cfg.json", {"periods": [0.0], "damping_ratio": 0.05})
        with self.assertRaisesRegex(InputError, "positive"):
            load_config(path)

    def test_damping_out_of_range_rejected(self):
        for damping in (-0.1, 1.0, 1.5):
            path = _write(
                self.dir, "cfg.json", {"periods": [0.5], "damping_ratio": damping}
            )
            with self.assertRaisesRegex(InputError, "damping"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
