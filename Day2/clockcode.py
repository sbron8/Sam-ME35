from machine import PWM, Pin
import time

# ==== Servo Setup ====
servo = PWM(Pin(4), freq=50, duty_u16=0)

def set_servo_angle(angle):
    """
    Map 0–180° to 0.5–2.5 ms pulses (standard mapping)
    0°   -> 500 µs
    180° -> 2500 µs
    """
    min_us = 500
    max_us = 2500
    pulse_us = min_us + (max_us - min_us) * angle / 180
    servo.duty_ns(int(pulse_us * 1000))  # µs → ns

# Map hour+minutes to angle (1 → 180°, 12 → 0°)
def time_to_angle(hour, minute):
    # Convert to 12h format
    hour = hour % 12
    if hour == 0:
        hour = 12

    # Add minute fraction (e.g., 3:30 = 3.5 hours)
    hour_fraction = hour + minute / 60.0

    # Map 1 → 180°, 12 → 0°
    angle = 180 - (hour_fraction - 1) * (180 / 11)
    return angle

# ==== Startup Calibration Pause ====
print("Setting servo to 0° for calibration. Attach horn now...")
set_servo_angle(0)
time.sleep(5)
print("Starting clock...")

# ==== Clock Loop ====
try:
    while True:
        local_time = time.localtime()
        hour = local_time[3]
        minute = local_time[4]

        angle = time_to_angle(hour, minute)
        print("Time: {:02d}:{:02d} -> Angle: {:.2f}".format(hour, minute, angle))
        set_servo_angle(angle)

        time.sleep(60)  # update every 10 seconds

except KeyboardInterrupt:
    print("Stopped by user")
finally:
    servo.deinit()
    print("Servo released")