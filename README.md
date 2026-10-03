# Oscillator Response Spectra

Single-degree-of-freedom (SDOF) response and response-spectra tool for
vibration records, using only the Python standard library. No plotting.

## Model

For each period `T` the tool integrates the unit-mass oscillator

```
u'' + 2*zeta*omega*u' + omega^2*u = -ag(t)
```

- `omega = 2*pi / T` — circular frequency (rad/s)
- `2*zeta*omega` — damping term, with damping ratio `zeta`
- `-ag(t)` — forcing, the negative of the ground acceleration
- initial relative displacement and velocity are zero; the initial relative
  acceleration follows from the equation of motion: `u''(0) = -ag(0)`

Absolute acceleration is `u'' + ag`. Peaks are maxima of absolute values
taken at the discrete sample times only (including the initial point); no
interpolation between steps is performed. The pseudo-acceleration spectrum
value is `omega^2 * max|u|`.

## Integration

Newmark average-acceleration method (constant acceleration within each
step): `gamma = 1/2` (velocity coefficient), `beta = 1/4` (displacement
coefficient). Each step uses its actual time increment `dt = t[i] - t[i-1]`,
so irregularly sampled records are integrated correctly and must not be
treated as uniformly sampled.

## Units

- time: seconds
- ground acceleration: m/s^2
- relative displacement: m
- relative velocity: m/s
- absolute / pseudo acceleration: m/s^2
- period: seconds; damping ratio: dimensionless, `0 <= zeta < 1`

## Input files

Time series JSON (strictly increasing time, at least two points, equal
length arrays, unequal spacing allowed):

```json
{"time": [0.0, 0.02, 0.05], "acceleration": [0.0, 0.4, -0.6]}
```

Configuration JSON (positive periods, damping ratio in `[0, 1)`):

```json
{"periods": [0.1, 0.5, 1.0], "damping_ratio": 0.05}
```

Invalid input is rejected with a message explaining the exact problem.

## Usage

```
python -m sdof record.json config.json --output-dir output
```

or, after `pip install .`, the `sdof-spectra` command.

Outputs per run:

- `history_T<period>s.csv` — time, relative displacement, relative velocity,
  absolute acceleration for each period
- `spectra.json` — per-period peaks (relative displacement, relative
  velocity, absolute acceleration) and the pseudo-acceleration spectrum

## Tests

```
python -m unittest discover -s tests -v
```

Covers zero input, a hand-computed single Newmark step, irregular
(variable-step) records against a reference recurrence and an analytic
solution, input validation, and the CLI end to end.
