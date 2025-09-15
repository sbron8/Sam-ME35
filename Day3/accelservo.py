from Day3 import lis3dh
from machine import Pin, PWM
import time

# ----- Servo setup -----
servo = PWM(Pin(4), freq=50)   # same pin/freq you just tested

def set_angle(angle):
    """
    Map 0–180° to duty_ns using the 0.5–2.5 ms range you proved works.
    """
    angle = max(0, min(180, angle))
    pulse_ms = 0.5 + (angle / 180) * 2.0   # 0.5 → 2.5 ms
    servo.duty_ns(int(pulse_ms * 1_000_000))

# ----- Accelerometer + servo -----
def demo():
    try:
        h3lis331dl = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)
        print("WHO AM I: 0x{:02X}".format(h3lis331dl.read_who_am_i()))

        while True:
            g = h3lis331dl.read_accl_g()
            ax = g['x']      # use X-axis tilt; swap to g['y'] if preferred

            # Map -1g…+1g to 0…180°
            angle = (ax + 1) * 90
            set_angle(angle)

            print("X = {:.2f}g  -> Servo = {:.0f}°".format(ax, angle))
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        servo.deinit()

demo()
