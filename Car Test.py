from machine import SoftI2C, Pin, PWM
import time
from veml6040 import VEML6040

# ---- Encoder + Motor classes ----
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
        self.M1 = PWM(Pin(m1), freq=8000, duty_u16=0)  # higher PWM frequency
        self.M2 = PWM(Pin(m2), freq=8000, duty_u16=0)
        self.stop()

    def stop(self):
        self.M1.duty_u16(0)
        self.M2.duty_u16(0)

    def start(self, direction=1, speed=60):  # faster sweep speed
        duty = int(speed * 65535 / 100)
        if direction == 1:
            self.M1.duty_u16(duty)
            self.M2.duty_u16(0)
        else:
            self.M1.duty_u16(0)
            self.M2.duty_u16(duty)

# ---- Motors ----
left_motor  = Motor(14, 27, 32, 39)
right_motor = Motor(12, 13, 25, 33)

# ---- Servo on Pin 19 ----
servo = PWM(Pin(19), freq=50)

def angle_to_duty(angle):
    min_duty = 1638
    max_duty = 8192
    return int(min_duty + (max_duty - min_duty) * angle / 180)

def move_servo(angle, hold_time=1):
    servo.duty_u16(angle_to_duty(angle))
    time.sleep(hold_time)
    servo.duty_u16(angle_to_duty(0))

# ---- Color sensor ----
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
color = VEML6040(i2c)
print("VEML6040 ready")

IT_40MS = (0b000 << 4)
color.set_integration_time(IT_40MS)

# ---- Parameters ----
BASE    = 60        # forward speed %
TURN    = 35        # sweep speed %
HALF_TURN = TURN / 2
SWEEP_STEP = 0.03   # shorter sleep → faster reading
SWEEP_TIME = 3.0    # longer sweep → wider range

COLOR_THRESHOLDS = {
    "white": (295, 335, 260, 292, 113, 122, 511, 567),
    "black": (151, 171, 123, 137, 53, 59, 284, 314),
    "red":   (125, 149, 91, 94, 41, 43, 242, 273),
    "green": (181, 184, 170, 171, 62, 63, 340, 341),
    "blue":  (141, 143, 126, 127, 67, 69, 282, 282),
}

# ---- Helper functions ----
def get_rgbw():
    color.trigger_measurement()
    r, g, b, w = color.read_rgbw()
    return r, g, b, w

def in_range(val, lo, hi):
    return lo <= val <= hi

def detect_color(r, g, b, w, black_thresh, white_thresh):
    if w < black_thresh:
        return "black"
    elif w > white_thresh:
        return "white"
    for label, (rmin, rmax, gmin, gmax, bmin, bmax, wmin, wmax) in COLOR_THRESHOLDS.items():
        if in_range(r, rmin, rmax) and in_range(g, gmin, gmax) and in_range(b, bmin, bmax) and in_range(w, wmin, wmax):
            return label
    return "unknown"

def calibrate_black_only():
    print("Calibrating... Place sensor on black line.")
    time.sleep(2)
    _, _, _, black_w = get_rgbw()
    print("Black reference:", black_w)
    white_sample_min = COLOR_THRESHOLDS["white"][6]
    white_sample_max = COLOR_THRESHOLDS["white"][7]
    white_ref = (white_sample_min + white_sample_max) / 2
    black_thresh = black_w + (white_ref - black_w) * 0.25
    white_thresh = white_ref - (white_ref - black_w) * 0.25
    print("Calibrated black threshold:", black_thresh)
    return black_thresh, white_thresh

# ---- Sweep logic ----
def directional_sweep(black_thresh):
    best_w = 9999
    best_pos = left_motor.enc.value()

    # Sweep left
    t_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t_start) < SWEEP_TIME * 1000:
        left_motor.start(direction=1, speed=TURN)
        right_motor.start(direction=-1, speed=TURN)
        _, _, _, w = get_rgbw()
        if abs(w - black_thresh) < abs(best_w - black_thresh):
            best_w = w
            best_pos = left_motor.enc.value()
        if w < black_thresh:
            left_motor.stop()
            right_motor.stop()
            return
        time.sleep(SWEEP_STEP)

    left_motor.stop()
    right_motor.stop()
    time.sleep(0.05)

    # Sweep right double distance
    t_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t_start) < SWEEP_TIME * 2 * 1000:
        left_motor.start(direction=-1, speed=TURN)
        right_motor.start(direction=1, speed=TURN)
        _, _, _, w = get_rgbw()
        if abs(w - black_thresh) < abs(best_w - black_thresh):
            best_w = w
            best_pos = left_motor.enc.value()
        if w < black_thresh:
            left_motor.stop()
            right_motor.stop()
            return
        time.sleep(SWEEP_STEP)

    left_motor.stop()
    right_motor.stop()
    time.sleep(0.05)

# ---- Main loop ----
black_thresh, white_thresh = calibrate_black_only()

while True:
    r, g, b, w = get_rgbw()
    detected = detect_color(r, g, b, w, black_thresh, white_thresh)
    print("Detected:", detected, "RGBW:", (r, g, b, w))

    if detected == "black":
        left_motor.start(direction=-1, speed=BASE)
        right_motor.start(direction=-1, speed=BASE)

    elif detected in ["white", "unknown"]:
        print("Lost line, performing directional sweep...")
        directional_sweep(black_thresh)
        left_motor.start(direction=-1, speed=BASE)
        right_motor.start(direction=-1, speed=BASE)

    elif detected in ["red", "green", "blue"]:
        left_motor.stop()
        right_motor.stop()
        time.sleep(0.5)
        if detected == "green":
            move_servo(30, hold_time=1)
        elif detected == "red":
            move_servo(90, hold_time=1)
        elif detected == "blue":
            move_servo(120, hold_time=1)
        left_motor.start(direction=-1, speed=BASE)
        right_motor.start(direction=-1, speed=BASE)
        time.sleep(0.5)

    else:
        left_motor.stop()
        right_motor.stop()

    time.sleep(0.05)
