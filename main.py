# Solar PV monitor with MPPT (Perturb & Observe)
# Raspberry Pi Pico, MicroPython, simulated on Wokwi
#
# Potentiometer on GP26  -> irradiance G (100..1000 W/m2)
# SSD1306 OLED on I2C0   -> GP4 (SDA), GP5 (SCL)
# LED on GP15            -> on when tracked power is within 2 % of the true MPP

import math
import time
from machine import ADC, I2C, Pin
from ssd1306 import SSD1306_I2C

# ---------------------------------------------------------------
# PV panel model: single-diode, ignoring series/shunt resistance
#   I = Iph - I0 * (exp(V / A) - 1),   Iph = Isc * G / 1000
# ---------------------------------------------------------------
VOC_STC = 22.0   # open-circuit voltage at 1000 W/m2 [V]  (36-cell panel)
ISC_STC = 8.0    # short-circuit current at 1000 W/m2 [A]
A = 1.21         # n * Ns * Vt  (ideality x cells x thermal voltage) [V]
I0 = ISC_STC / (math.exp(VOC_STC / A) - 1)   # saturation current [A]


def pv_current(v, g):
    i = ISC_STC * g / 1000 - I0 * (math.exp(v / A) - 1)
    return i if i > 0 else 0.0


def pv_voc(g):
    return A * math.log(ISC_STC * g / 1000 / I0 + 1)


def true_mpp(g):
    """Brute-force scan of the P-V curve: the 'theoretical' maximum."""
    voc = pv_voc(g)
    best_p = 0.0
    best_v = 0.0
    v = 0.0
    while v < voc:
        p = v * pv_current(v, g)
        if p > best_p:
            best_p = p
            best_v = v
        v += 0.1
    return best_p, best_v


# ---------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------
pot = ADC(26)
led = Pin(15, Pin.OUT)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# ---------------------------------------------------------------
# Perturb & Observe state
# ---------------------------------------------------------------
STEP = 0.2       # perturbation size [V]
step = STEP
v = 12.0         # operating voltage (on real hardware: set by converter duty cycle)
p_prev = 0.0
t0 = time.ticks_ms()

print("t_ms,G,V,I,P,Pmax,Vmpp,eff")

while True:
    # 1. "Measure": irradiance from the pot, current from the PV model
    g = 100 + pot.read_u16() / 65535 * 900
    i = pv_current(v, g)
    p = v * i

    # 2. Theoretical maximum for comparison
    pmax, vmpp = true_mpp(g)
    eff = 100 * p / pmax if pmax > 0 else 0.0

    # 3. Display
    oled.fill(0)
    oled.text("SOLAR PV  MPPT", 0, 0)
    oled.text("G=%4d W/m2" % int(g), 0, 8)
    oled.text("V=%5.2f I=%4.2f" % (v, i), 0, 16)
    oled.text("P=%6.1f W" % p, 0, 24)
    oled.text("Pmax=%6.1f W" % pmax, 0, 32)
    oled.text("Eff=%5.1f %%" % eff, 0, 40)
    oled.rect(0, 56, 128, 8, 1)
    oled.fill_rect(0, 56, int(128 * p / pmax) if pmax > 0 else 0, 8, 1)
    oled.show()

    led.value(1 if eff >= 98 else 0)

    # 4. CSV log for plotting later
    print("{},{:.0f},{:.2f},{:.2f},{:.1f},{:.1f},{:.2f},{:.1f}".format(
        time.ticks_diff(time.ticks_ms(), t0), g, v, i, p, pmax, vmpp, eff))

    # 5. Perturb & Observe: keep going while power rises, reverse when it falls
    if p < p_prev:
        step = -step
    p_prev = p
    v += step
    v = min(max(v, 0.5), pv_voc(g) - 0.1)

    time.sleep_ms(100)
