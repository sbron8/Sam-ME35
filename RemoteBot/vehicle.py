"""MicroPython ESP-NOW receiver that drives a differential car.

The vehicle listens for JSON packets from ``RemoteBot/controller.py``.
Each message contains a ``throttle`` field (-1 reverse, 0 stop, 1 forward)
and a ``steering`` field (0-180 degrees).  Throttle is converted into H-bridge
outputs that drive two brushed DC motors (sharing the same throttle command)
while steering is translated into servo pulse widths. Motor encoder channels
are counted so you can monitor wheel activity from the serial console.
"""

import time
import ujson
import network
import espnow
from machine import Pin, PWM


# === User configuration ====================================================
# MAC address for the handheld controller (printed with ``print_mac`` below).
# Replace with your controller's STA interface MAC address.
CONTROLLER_MAC = b"\xff\xff\xff\xff\xff\xff"

# GPIO assignments for the vehicle hardware.
# Motor driver channels. Each motor uses two inputs so we can drive forward or
# reverse by modulating the corresponding PWM pin.
MOTOR1_FORWARD_PIN = 13
MOTOR1_REVERSE_PIN = 12
MOTOR2_FORWARD_PIN = 27
MOTOR2_REVERSE_PIN = 14

# Quadrature encoders connected to the motors.
ENCODER1_A_PIN = 32
ENCODER1_B_PIN = 39
ENCODER2_A_PIN = 21
ENCODER2_B_PIN = 22

SERVO_PIN = 15
STATUS_LED_PIN = 2

# Motor tuning parameters.
PWM_FREQ = 1000
PWM_DUTY = 512  # 10-bit duty cycle (range 0-1023)
STOP_TIMEOUT_MS = 1000  # failsafe stop if no packet received

# Servo configuration for a typical hobby servo (50 Hz PWM).
SERVO_FREQ = 50
SERVO_MIN_US = 600
SERVO_MAX_US = 2400
SERVO_FRAME_US = 20000


# === Helper utilities ======================================================
def print_mac(label: str, wlan: network.WLAN) -> None:
    mac = ":".join("%02X" % b for b in wlan.config("mac"))
    print("{} MAC: {}".format(label, mac))


def angle_to_duty(angle: int) -> int:
    """Convert a steering angle (0-180) into a duty_u16 value."""
    pulse_us = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * angle // 180
    duty = int((pulse_us * 65535) // SERVO_FRAME_US)
    return min(65535, max(0, duty))


def apply_motor_direction(forward_pwm: PWM, reverse_pwm: PWM, throttle: int) -> None:
    """Drive a single motor using two H-bridge inputs."""
    if throttle > 0:
        forward_pwm.duty(PWM_DUTY)
        reverse_pwm.duty(0)
    elif throttle < 0:
        forward_pwm.duty(0)
        reverse_pwm.duty(PWM_DUTY)
    else:
        forward_pwm.duty(0)
        reverse_pwm.duty(0)


def apply_throttle(throttle: int) -> None:
    """Apply the same throttle command to both drive motors."""
    apply_motor_direction(motor1_forward_pwm, motor1_reverse_pwm, throttle)
    apply_motor_direction(motor2_forward_pwm, motor2_reverse_pwm, throttle)


def encoder_callback(counter: list, pin: Pin) -> None:
    """Interrupt handler that increments a mutable counter."""
    counter[0] += 1


# === Hardware bring-up =====================================================
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()
print_mac("Vehicle", sta)

radio = espnow.ESPNow()
radio.active(True)
try:
    radio.add_peer(CONTROLLER_MAC)
except OSError:
    pass

motor1_forward_pwm = PWM(Pin(MOTOR1_FORWARD_PIN), freq=PWM_FREQ, duty=0)
motor1_reverse_pwm = PWM(Pin(MOTOR1_REVERSE_PIN), freq=PWM_FREQ, duty=0)
motor2_forward_pwm = PWM(Pin(MOTOR2_FORWARD_PIN), freq=PWM_FREQ, duty=0)
motor2_reverse_pwm = PWM(Pin(MOTOR2_REVERSE_PIN), freq=PWM_FREQ, duty=0)

servo = PWM(Pin(SERVO_PIN), freq=SERVO_FREQ)
servo.duty_u16(angle_to_duty(90))
status_led = Pin(STATUS_LED_PIN, Pin.OUT, value=0)

encoder1_count = [0]
encoder2_count = [0]

encoder1_a = Pin(ENCODER1_A_PIN, Pin.IN)
encoder1_b = Pin(ENCODER1_B_PIN, Pin.IN)
encoder2_a = Pin(ENCODER2_A_PIN, Pin.IN)
encoder2_b = Pin(ENCODER2_B_PIN, Pin.IN)

encoder1_a.irq(handler=lambda pin: encoder_callback(encoder1_count, pin), trigger=Pin.IRQ_RISING)
encoder1_b.irq(handler=lambda pin: encoder_callback(encoder1_count, pin), trigger=Pin.IRQ_RISING)
encoder2_a.irq(handler=lambda pin: encoder_callback(encoder2_count, pin), trigger=Pin.IRQ_RISING)
encoder2_b.irq(handler=lambda pin: encoder_callback(encoder2_count, pin), trigger=Pin.IRQ_RISING)


# === Main control loop =====================================================
last_packet_time = time.ticks_ms()
throttle = 0
steering = 90
last_encoder_report = time.ticks_ms()

while True:
    _host, msg = radio.irecv(timeout=50)
    if msg:
        status_led.value(1)
        last_packet_time = time.ticks_ms()
        try:
            data = ujson.loads(msg)
            throttle = int(data.get("throttle", throttle))
            steering = int(data.get("steering", steering))
        except (ValueError, TypeError):
            # Ignore malformed packets but keep the failsafe timer alive.
            pass

    # Apply the latest command data.
    apply_throttle(throttle)
    servo.duty_u16(angle_to_duty(steering))

    # Trigger failsafe stop if no command has been received recently.
    if time.ticks_diff(time.ticks_ms(), last_packet_time) > STOP_TIMEOUT_MS:
        throttle = 0
        apply_throttle(0)
        status_led.value(0)

    if time.ticks_diff(time.ticks_ms(), last_encoder_report) > 1000:
        print("Encoders: M1={}, M2={}".format(encoder1_count[0], encoder2_count[0]))
        encoder1_count[0] = 0
        encoder2_count[0] = 0
        last_encoder_report = time.ticks_ms()

    time.sleep_ms(20)
