"""MicroPython remote controller for ESP-NOW driven car.

This script configures an ESP32-based handheld controller with two
momentary buttons that request forward and reverse motion plus an
analog input (potentiometer) that sets the steering angle.  Commands are
broadcast over ESP-NOW as JSON payloads with three unique throttling
states: forward, reverse, and stop.  The steering angle is encoded as a
0-180 degree value so the remote vehicle can command a standard hobby
servo.
"""

import time
import ujson
import network
import espnow
from machine import Pin, ADC


# === User configuration ====================================================
# MAC address for the remote vehicle's WiFi interface.
# Replace with the MAC address printed by ``RemoteBot/vehicle.py`` during its
# boot sequence.
VEHICLE_MAC = b"\xff\xff\xff\xff\xff\xff"

# GPIO assignments for the handheld controller hardware.
FORWARD_PIN = 12  # momentary button, active-low
REVERSE_PIN = 14  # momentary button, active-low
STEER_POT_PIN = 34  # potentiometer providing steering command

# Debounce/filter tuning.
POLL_DELAY_MS = 80
STEER_DEADBAND = 1  # degrees; prevents noisy updates


# === ESP-NOW bootstrap =====================================================
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()

radio = espnow.ESPNow()
radio.active(True)

# The ESP-NOW implementation ignores duplicate peers, so it is safe to add
# the peer at every boot.
try:
    radio.add_peer(VEHICLE_MAC)
except OSError:
    # Already paired; nothing to do.
    pass


# === Input devices =========================================================
forward_button = Pin(FORWARD_PIN, Pin.IN, Pin.PULL_UP)
reverse_button = Pin(REVERSE_PIN, Pin.IN, Pin.PULL_UP)
steering_input = ADC(Pin(STEER_POT_PIN))
steering_input.atten(ADC.ATTN_11DB)  # full 0-3.3 V range


# === Helper functions ======================================================
def read_throttle() -> int:
    """Return -1 for reverse, 0 for stop, +1 for forward."""
    forward_pressed = not forward_button.value()
    reverse_pressed = not reverse_button.value()

    if forward_pressed and not reverse_pressed:
        return 1
    if reverse_pressed and not forward_pressed:
        return -1
    return 0


def read_steering() -> int:
    """Read the potentiometer and return an angle in the range [0, 180]."""
    raw = steering_input.read_u16()
    angle = int((raw * 180) // 65535)
    return min(180, max(0, angle))


# === Main loop =============================================================
last_payload = None
last_angle = read_steering()

while True:
    throttle = read_throttle()
    angle = read_steering()

    # Limit the frequency of steering updates by applying a deadband.
    if abs(angle - last_angle) <= STEER_DEADBAND:
        angle = last_angle
    else:
        last_angle = angle

    payload = ujson.dumps({"throttle": throttle, "steering": angle})

    if payload != last_payload:
        try:
            radio.send(VEHICLE_MAC, payload, sync=True)
            last_payload = payload
        except OSError:
            # Transient radio error—try again on the next cycle.
            pass

    time.sleep_ms(POLL_DELAY_MS)
