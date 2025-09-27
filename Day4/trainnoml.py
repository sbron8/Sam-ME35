from machine import Pin, PWM
import time
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

# ---------------- Setup -----------------
motor = Motor(14, 27, 32, 39)
accel = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)

STATE_TRAIN = True
refs = {"forward": None, "stop": None, "back": None}
order = ["forward", "stop", "back"]   # training sequence
count = 0
last_time = 0
debounce = 150

def trainButton(pin):
    global count, last_time
    if time.ticks_ms() - last_time < debounce: return
    last_time = time.ticks_ms()
    if count < 3:
        refs[order[count]] = accel.read_accl_g()['x']
        print(f"Trained {order[count]}: {refs[order[count]]:.3f} g")
        count += 1
    else:
        print("All three states recorded.")

def playButton(pin):
    global STATE_TRAIN, last_time
    if time.ticks_ms() - last_time < debounce: return
    last_time = time.ticks_ms()
    if count == 3:
        STATE_TRAIN = False
        print("Play mode active.")
    else:
        print("Finish training all 3 states first.")

Pin(35, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_RISING, handler=trainButton)
Pin(34, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_RISING, handler=playButton)

# ---------------- Main Loop -----------------
while True:
    if STATE_TRAIN:
        time.sleep(0.1)
        continue

    xg = accel.read_accl_g()['x']

    # Simple distance-to-reference classification
    dist = {state: abs(xg - refs[state]) for state in refs}
    action = min(dist, key=dist.get)

    if action == "forward":
        motor.start(direction=1, speed=50)
    elif action == "back":
        motor.start(direction=-1, speed=50)
    else:  # "stop"
        motor.stop()

    time.sleep(0.05)
