from machine import PWM, Pin
import network
import urequests
import time
from Day2 import secrets  # contains SSID and PWD

# ==== Servo Setup ====
servo = PWM(Pin(4), freq=50, duty_u16=0)

def set_servo_angle(angle):
    """
    Map 0–180° to 0.5–2.5 ms pulses
    """
    min_us = 500    # 0°
    max_us = 2500   # 180°
    pulse_us = min_us + (max_us - min_us) * angle / 180
    servo.duty_ns(int(pulse_us * 1000))

# ==== Button Setup ====
button = Pin(35, Pin.IN)  # D35 onboard button

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
    # Coordinates for Boston, MA
    latitude = 42.3601
    longitude = -71.0589
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"

    try:
        response = urequests.get(url)
        if response.status_code == 200:
            data = response.json()
            condition = data["current_weather"]["weathercode"]
            print("Weather condition code:", condition)
            return condition
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print("Request failed:", e)
        return None
    finally:
        try:
            response.close()
        except:
            pass

# ==== Map Weather to Servo Angles ====
def weather_to_angle(condition):
    """
    Map weather condition code to servo angle.
    Corrected reversed positions:
    Sun    -> 160°
    Rain   -> 110°
    Cloudy -> 50°
    Snow   -> 30°
    """
    if condition in [0, 1]:         # Clear / Mainly clear
        return 160
    elif condition in [2, 3]:       # Partly cloudy / Overcast
        return 65
    elif condition in [61, 63, 65, 66, 67]:  # Rain
        return 110
    elif condition in [71, 73, 75, 77, 85, 86]:  # Snow
        return 30
    else:
        return 160  # Default to sun if unknown

# ==== Main Loop ====
print("Press the button to check weather and move servo...")

while True:
    if button.value() == 0:  # button pressed
        condition = fetch_weather()
        if condition is not None:
            angle = weather_to_angle(condition)
            print(f"Moving servo to {angle} degrees for condition code {condition}")
            set_servo_angle(angle)
        time.sleep(1)  # debounce
    time.sleep(0.1)
