from machine import PWM, Pin
import network
import urequests
import time
from Day2 import secrets  # contains SSID and PWD

# ==== Servo Setup ====
servo = PWM(Pin(4), freq=50, duty_u16=0)

def set_servo_angle(angle):
    min_us = 500
    max_us = 2500
    pulse_us = min_us + (max_us - min_us) * angle / 180
    servo.duty_ns(int(pulse_us * 1000))

def time_to_angle(hour, minute):
    hour = hour % 12
    if hour == 0:
        hour = 12
    hour_fraction = hour + minute / 60.0
    angle = 180 - (hour_fraction - 1) * (180 / 11)
    return angle

# ==== Button Setup ====
button = Pin(35, Pin.IN)

# ==== Wi-Fi Setup ====
def wifi_connect():
    sta_if = network.WLAN(network.WLAN.IF_STA)
    if not sta_if.isconnected():
        print("Connecting to Wi-Fi...")
        sta_if.active(True)
        sta_if.connect(secrets.SSID, secrets.PWD)
        while not sta_if.isconnected():
            pass
    print("Network config:", sta_if.ifconfig())

wifi_connect()

# ==== Weather API Setup ====
def fetch_weather():
    latitude = 42.3601
    longitude = -71.0589
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            condition = response.json()["current_weather"]["weathercode"]
            return condition
    except:
        return None
    finally:
        try:
            response.close()
        except:
            pass
    return None

def weather_to_angle(condition):
    if condition in [0, 1]:
        return 160  # Sun
    elif condition in [2, 3]:
        return 65   # Cloudy
    elif condition in [61, 63, 65, 66, 67]:
        return 110  # Rain
    elif condition in [71, 73, 75, 77, 85, 86]:
        return 30   # Snow
    else:
        return 160  # default Sun

# ==== Startup Calibration ====
print("Calibration: Servo to 0°...")
set_servo_angle(0)
time.sleep(5)
print("Starting clock...")

# ==== Main Loop ====
try:
    while True:
        # --- Clock ---
        local_time = time.localtime()
        hour = local_time[3]
        minute = local_time[4]
        angle = time_to_angle(hour, minute)
        set_servo_angle(angle)

        # --- Check Button ---
        if button.value() == 0:
            print("Button pressed: show weather")
            condition = fetch_weather()
            if condition is not None:
                weather_angle = weather_to_angle(condition)
                print(f"Weather condition {condition}, angle {weather_angle}")
                set_servo_angle(weather_angle)
                time.sleep(8)  # hold weather for 8 seconds
            print("Returning to clock")

        time.sleep(1)

except KeyboardInterrupt:
    print("Stopped by user")
finally:
    servo.deinit()
    print("Servo released")
