from machine import Pin, PWM
import time
import math
from Day3 import lis3dh

# ---------------- Motor with Encoder -----------------
class Count:
    def __init__(self, A, B):
        self.A = Pin(A, Pin.IN)
        self.B = Pin(B, Pin.IN)
        self.counter = 0
        self.A.irq(self.cb, Pin.IRQ_RISING | Pin.IRQ_FALLING)
        self.B.irq(self.cb, Pin.IRQ_RISING | Pin.IRQ_FALLING)

    def cb(self, pin):
        other, inc = (self.B, 1) if pin == self.A else (self.A, -1)
        self.counter += -inc if pin.value() != other.value() else inc

    def value(self):
        return self.counter


class Motor:
    def __init__(self, m1, m2, A, B):
        self.enc = Count(A, B)
        self.M1 = PWM(Pin(m1), freq=100, duty_u16=0)
        self.M2 = PWM(Pin(m2), freq=100, duty_u16=0)
        self.stop()

    def stop(self):
        self.M1.duty_u16(0)
        self.M2.duty_u16(0)

    def start(self, direction=1, speed=50):
        duty = int(speed * 65535 / 100)
        if direction == 1:     # forward
            self.M1.duty_u16(duty)
            self.M2.duty_u16(0)
        else:                  # backward
            self.M1.duty_u16(0)
            self.M2.duty_u16(duty)

# ---------------- KNN Helper -----------------
def knn_predict(data, x, k=3):
    """data = [(value, label), ...]"""
    dists = sorted(data, key=lambda p: abs(p[0] - x))
    k_nearest = [label for _, label in dists[:k]]
    return max(set(k_nearest), key=k_nearest.count)

# ---------------- Setup -----------------
motor = Motor(14, 27, 32, 39)
accel = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)

STATE_TRAIN = True
order = ["forward", "stop", "back"]
samples = []                           # (x_value, label)
current_label_index = 0

last_time = 0
debounce = 150

def trainButton(pin):
    global current_label_index, last_time, samples
    if time.ticks_ms() - last_time < debounce:
        return
    last_time = time.ticks_ms()

    if current_label_index < len(order):
        label = order[current_label_index]
        xg = accel.read_accl_g()['x']
        samples.append((xg, label))
        print(f"Sample {label}: {xg:.3f} g")

        # collect ~10 samples per label
        if sum(1 for _, l in samples if l == label) >= 10:
            current_label_index += 1
            if current_label_index < len(order):
                print(f"Now training {order[current_label_index]}")
            else:
                print("All classes recorded.")
    else:
        print("Training complete—switch to Play mode.")

def playButton(pin):
    global STATE_TRAIN, last_time
    if time.ticks_ms() - last_time < debounce:
        return
    last_time = time.ticks_ms()
    if current_label_index >= len(order):
        STATE_TRAIN = False
        print("Play mode active.")
    else:
        print("Finish training all classes first.")

Pin(35, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_RISING, handler=trainButton)
Pin(34, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_RISING, handler=playButton)

# ----------- Speed Mapping from Y Tilt ------------
def y_to_speed(yg):
    """
    Map Y-axis tilt to a 0–100% speed.
    - |yg| <= 0.1 g  → 0 % (deadband)
    - |yg| >= 1.0 g  → 100 %
    """
    val = max(0, min(1.0, abs(yg)))       # clamp 0–1 g
    val = max(0, val - 0.1) / 0.9         # deadband
    return int(val * 100)

# ---------------- Main Loop -----------------
while True:
    if STATE_TRAIN:
        time.sleep(0.1)
        continue

    g = accel.read_accl_g()
    xg, yg = g['x'], g['y']

    action = knn_predict(samples, xg, k=3)
    speed = y_to_speed(yg)

    if action == "forward":
        motor.start(direction=1, speed=speed)
    elif action == "back":
        motor.start(direction=-1, speed=speed)
    else:
        motor.stop()

    time.sleep(0.05)
