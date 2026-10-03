import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from sdof.cli import main


class CliEndToEndTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, payload):
        path = self.dir / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_run_produces_histories_and_spectra(self):
        record = self._write(
            "record.json",
            {
                "time": [0.0, 0.02, 0.05, 0.09, 0.14, 0.2],
                "acceleration": [0.0, 0.4, -0.6, 0.3, -0.2, 0.1],
            },
        )
        config = self._write(
            "config.json", {"periods": [0.1, 0.5], "damping_ratio": 0.05}
        )
        out_dir = self.dir / "out"
        exit_code = main(
            [str(record), str(config), "--output-dir", str(out_dir)]
        )
        self.assertEqual(exit_code, 0)

        for period in (0.1, 0.5):
            csv_path = out_dir / f"history_T{period:g}s.csv"
            self.assertTrue(csv_path.exists())
            with open(csv_path, newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(len(rows), 7)  # header + 6 samples
            self.assertEqual(rows[1][1:], ["0.0", "0.0", "0.0"])

        spectra = json.loads((out_dir / "spectra.json").read_text(encoding="utf-8"))
        self.assertEqual(len(spectra), 2)
        for entry, period in zip(spectra, (0.1, 0.5)):
            self.assertEqual(entry["period_s"], period)
            omega = 2.0 * math.pi / period
            expected = omega * omega * entry["peak_relative_displacement_m"]
            self.assertAlmostEqual(
                entry["pseudo_acceleration_m_per_s2"], expected
            )

    def test_zero_record_gives_zero_spectra(self):
        record = self._write(
            "record.json",
            {"time": [0.0, 0.1, 0.2], "acceleration": [0.0, 0.0, 0.0]},
        )
        config = self._write(
            "config.json", {"periods": [0.3], "damping_ratio": 0.05}
        )
        out_dir = self.dir / "out"
        self.assertEqual(main([str(record), str(config), "--output-dir", str(out_dir)]), 0)
        spectra = json.loads((out_dir / "spectra.json").read_text(encoding="utf-8"))
        entry = spectra[0]
        self.assertEqual(entry["peak_relative_displacement_m"], 0.0)
        self.assertEqual(entry["peak_absolute_acceleration_m_per_s2"], 0.0)
        self.assertEqual(entry["pseudo_acceleration_m_per_s2"], 0.0)

    def test_invalid_input_reports_error(self):
        record = self._write(
            "record.json",
            {"time": [0.0, 0.0], "acceleration": [0.0, 0.0]},
        )
        config = self._write(
            "config.json", {"periods": [0.3], "damping_ratio": 0.05}
        )
        exit_code = main([str(record), str(config), "--output-dir", str(self.dir / "o")])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
