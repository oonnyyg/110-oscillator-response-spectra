# Oscillator Response Spectra

Single-degree-of-freedom (SDOF) response and response spectra from a
ground acceleration record. Pure Python standard library, no plotting.

## Units

- Time: seconds (`s`), strictly increasing, at least two points;
  unequal spacing is allowed and integrated with the actual step sizes.
- Ground acceleration: `m/s^2`.
- Output: relative displacement `m`, relative velocity `m/s`,
  absolute acceleration `m/s^2`.

## Model and integration

For each period `T` the unit-mass oscillator

    u'' + 2*zeta*omega*u' + omega^2*u = -ag(t)

is solved with `omega = 2*pi/T`, damping term `2*zeta*omega`, and the
negative of the ground acceleration as forcing. Initial relative
displacement and velocity are zero; the initial relative acceleration
satisfies the equation of motion at `t0`.

Integration uses the Newmark average acceleration method
(gamma = 1/2, beta = 1/4), advancing each interval with its actual
`dt = t[i] - t[i-1]`; irregular records are never resampled onto a
uniform grid. Peaks are maxima of absolute values over the discrete
time points only (including the initial point), with no interpolation
between steps.

The pseudo-acceleration spectrum is `Psa = omega^2 * Sd`, where `Sd`
is the peak relative displacement.

## Usage

    python main.py config.json

Config:

```json
{
  "record_file": "record.json",
  "periods": [0.1, 0.5, 1.0, 2.0],
  "damping": 0.05,
  "output_dir": "out"
}
```

Record JSON (`record.json`):

```json
{"time": [0.0, 0.01, 0.02], "acceleration": [0.0, 0.15, -0.1]}
```

Validation: periods must be positive; damping must satisfy
`0 < zeta < 1`; time must be strictly increasing with at least two
points. Invalid input produces a clear error message on stderr.

Outputs (in `output_dir`):

- `history_T<period>s.csv` — time, relative displacement, relative
  velocity, absolute acceleration (relative + ground) per period.
- `spectra.json` — per-period peaks (Sd, Sv, Sa) and
  pseudo-acceleration, with units and damping ratio.

## Tests

    python -m unittest test_sdof -v

Covers zero input, a hand-verified single Newmark step, variable time
step behavior, input validation, and spectrum consistency.
