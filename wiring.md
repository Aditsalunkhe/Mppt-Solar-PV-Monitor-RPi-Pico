# Wiring

Board: **Raspberry Pi Pico** (Wokwi part `wokwi-pi-pico`), MicroPython firmware.
The complete circuit is in [`wokwi/diagram.json`](../wokwi/diagram.json); paste it into the
`diagram.json` tab of a new Wokwi project.

## Connections

| Part | Part pin | Pico pin | Purpose |
|---|---|---|---|
| Potentiometer | SIG | GP26 (ADC0) | Irradiance input ("the sun") |
| Potentiometer | VCC | 3V3 | Reference supply |
| Potentiometer | GND | GND | Ground |
| SSD1306 OLED (128×64) | SDA | GP4 (I2C0 SDA) | Display data |
| SSD1306 OLED | SCL | GP5 (I2C0 SCL) | Display clock |
| SSD1306 OLED | VCC | 3V3 | Supply |
| SSD1306 OLED | GND | GND | Ground |
| LED (green) + 220 Ω | anode via resistor | GP15 | "At maximum power point" indicator |
| LED | cathode | GND | Ground |

## Notes

- The OLED is addressed at `0x3C` over I²C at 400 kHz.
- `ADC.read_u16()` returns 0–65535 (the 12-bit ADC result scaled to 16 bits). The code maps
  that linearly to 100–1000 W/m².
- The LED draws roughly (3.3 V − ~2 V) / 220 Ω ≈ 6 mA from GP15.
- The potentiometer stands in for a real irradiance sensor, and the panel current is
  computed from the model rather than measured. On real hardware, measure panel voltage
  with a resistor divider and current with a sensor such as an INA219 or ACS712, and set
  the operating point with a buck/boost converter driven by PWM.
