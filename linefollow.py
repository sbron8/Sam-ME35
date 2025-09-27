from machine import SoftI2C, Pin, PWM
import time
from veml6040 import VEML6040

# ---- Encoder + Motor classes (unchanged) ----
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
        self.M1.duty_u16(0); self.M2.duty_u16(0)
    def start(self, direction=1, speed=50):
        duty = int(speed * 65535 / 100)
        if direction == 1:
            self.M1.duty_u16(duty); self.M2.duty_u16(0)
        else:
            self.M1.duty_u16(0);    self.M2.duty_u16(duty)

# ---- Motors ----
left_motor  = Motor(14, 27, 32, 39)
right_motor = Motor(12, 13, 25, 33)

# ---- Color sensor ----
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
color = VEML6040(i2c)
print("VEML6040 ready")

# ---- Parameters ----
BASE    = 30     # forward speed %
TURN    = 20     # sweep turn speed %
THRESH  = 14000  # brightness threshold (tune!)
SWEEP_T = 2    # seconds per half-sweep

def brightness():
    color.trigger_measurement()
    _, _, _, w = color.read_rgbw()
    return w

# ---- Main loop with left-right sweep ----
lost_dir = -1           # start sweeping left
last_flip = time.ticks_ms()

while True:
    w = brightness()
    print("White:", w)

    if w < THRESH:                       # black tape detected
        left_motor.start(direction=-1, speed=BASE)
        right_motor.start(direction=-1, speed=BASE)
        lost_dir = -1                    # reset to left first next time
    else:                                # lost line → sweep
        now = time.ticks_ms()
        # flip sweep direction every SWEEP_T seconds
        if time.ticks_diff(now, last_flip) > SWEEP_T * 1000:
            lost_dir *= -1
            last_flip = now

        if lost_dir == -1:   # rotate left
            left_motor.start(direction=1,  speed=TURN)
            right_motor.start(direction=-1, speed=TURN)
        else:                # rotate right
            left_motor.start(direction=-1, speed=TURN)
            right_motor.start(direction=1,  speed=TURN)

    time.sleep(0.05)

