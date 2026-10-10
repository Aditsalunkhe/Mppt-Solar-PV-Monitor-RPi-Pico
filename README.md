# Solar PV Monitor with MPPT (Perturb & Observe) on Raspberry Pi Pico

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![MicroPython](https://img.shields.io/badge/MicroPython-Raspberry%20Pi%20Pico-blue)
![Simulation](https://img.shields.io/badge/Simulated%20on-Wokwi-orange)

A solar panel only delivers its maximum power at one particular operating voltage, and that
voltage moves as the sunlight changes. This project simulates a PV panel with a single-diode
model and uses a **Perturb & Observe (P&O) Maximum Power Point Tracker** to follow that moving
peak. A potentiometer stands in for the sun, and an OLED shows voltage, current, power, the
theoretical maximum and the tracking efficiency in real time.

**Live simulation:** https://wokwi.com/projects/477459931358690305

## What it demonstrates

- Single-diode PV modelling: I–V and P–V curves that shift with irradiance
- Maximum power point tracking with P&O, including its steady-state oscillation
- A brute-force reference (theoretical maximum) so tracking efficiency is measured, not assumed
- Embedded implementation on a Raspberry Pi Pico in MicroPython: ADC input, I²C OLED, GPIO
- Serial CSV logging and offline analysis

## How it works

Every 100 ms the program:

1. Reads the potentiometer (ADC) and maps it to irradiance, 100–1000 W/m².
2. Computes panel current at the present voltage from the PV model, then power P = V × I.
3. Scans the whole P–V curve to find the true maximum power and its voltage.
4. Shows V, I, P, Pmax and efficiency on the OLED, lights the LED when within 2% of the maximum,
   and prints a CSV line over serial.
5. Compares P with the previous cycle: if it dropped, the voltage step reverses; then V changes
   by 0.2 V.

The equations and a flowchart are in [`theory.md`](theory.md).

## Hardware (simulated)

| Component | Role |
|---|---|
| Raspberry Pi Pico | Controller (MicroPython) |
| Potentiometer on GP26 | Irradiance input |
| SSD1306 128×64 OLED on I²C (GP4/GP5) | Live display |
| LED + 220 Ω on GP15 | "At maximum power point" indicator |

Full pin table: [`wiring.md`](wiring.md).

## Run it in Wokwi

1. On [wokwi.com](https://wokwi.com) create a new **Raspberry Pi Pico → MicroPython** project.
2. Replace the contents of the `diagram.json` tab with [`diagram.json`](diagram.json).
3. Add a new file `ssd1306.py` and paste [`ssd1306.py`](ssd1306.py).
4. Replace `main.py` with [`main.py`](main.py).
5. Press **Play** and turn the potentiometer. Open the serial monitor to see the CSV log
   (`t_ms,G,V,I,P,Pmax,Vmpp,eff`).

## Reproduce the results without Wokwi

```bash
pip install -r analysis/requirements.txt
python analysis/simulate_mppt.py
```

This re-runs the same model and P&O update in CPython, rewrites `sample_run.csv` and
regenerates both figures. It is a re-implementation of the algorithm in `main.py`, not a
capture from the Wokwi serial monitor.

## Results

I–V and P–V curves of the modelled 36-cell panel. The maximum power point moves as irradiance
changes:

![PV curves](pv_curves.png)

Irradiance is stepped 1000 → 550 → 235 → 100 → 1000 W/m². The tracker re-converges within a few
seconds each time and then oscillates by about ±0.2 V around the true peak:

![Tracking](tracking.png)

Settled operating points (end of each 10 s segment):

| Irradiance (W/m²) | Tracked V (V) | Tracked P (W) | True max P (W) | Worst efficiency in last 2 s |
|---|---|---|---|---|
| 1000 | 18.60 | 139.8 | 139.8 | 99.9 % |
| 550 | 18.20 | 73.8 | 73.9 | 99.8 % |
| 235 | 17.00 | 29.8 | 29.8 | 99.8 % |
| 100 | 15.80 | 11.9 | 11.9 | 99.9 % |

"Efficiency" here means tracked power divided by the true maximum power of the same modelled
panel. It is not the panel's conversion efficiency.

## Limitations

- Simulation only; not tested on physical hardware.
- The PV model ignores series and shunt resistance and temperature, and has a single power peak
  (no partial shading).
- Operating voltage is set directly in code. A real system sets it through a DC–DC converter.
- Panel current is computed, not measured.
- P&O can move the wrong way if irradiance changes faster than the loop, and it always ripples
  around the peak.

## Possible extensions

- Add a temperature input and shift $V_{oc}$ and $I_{sc}$ accordingly
- Implement Incremental Conductance or an adaptive step size and compare ripple and response time
- Model a buck converter and drive its duty cycle from the tracker
- Add battery state-of-charge tracking and energy (Wh) logging
- Move from simulated to measured values using an INA219 current sensor

## References

1. T. Esram and P. L. Chapman, "Comparison of Photovoltaic Array Maximum Power Point Tracking
   Techniques," *IEEE Trans. Energy Conversion*, vol. 22, no. 2, pp. 439–449, 2007.
2. M. G. Villalva, J. R. Gazoli and E. Ruppert F., "Comprehensive Approach to Modeling and
   Simulation of Photovoltaic Arrays," *IEEE Trans. Power Electronics*, vol. 24, no. 5,
   pp. 1198–1208, 2009.

## License

MIT, see [`LICENSE`](LICENSE).
