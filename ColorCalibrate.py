import time
from machine import SoftI2C, Pin
from veml6040 import VEML6040

# I2C setup
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
sensor = VEML6040(i2c)

IT_40MS = (0b000 << 4) # 40 ms
sensor.set_integration_time(IT_40MS)

# Colors to record
colors = ["white", "black", "red", "green", "blue"]

# Storage for dataset
dataset = []

print("Starting color logger...")
print("You will take 2 samples for each color.")
print("Output will be in CSV format: red,green,blue,white,label")

for color in colors:
    for i in range(2):
        input(f"Place sensor on {color.upper()} (sample {i+1}) and press Enter...")
        sensor.trigger_measurement()
        r, g, b, w = sensor.read_rgbw()
        dataset.append((r, g, b, w, color))
        print(f"Recorded {color} sample {i+1}: {r},{g},{b},{w},{color}")

print("All samples recorded! Here’s your dataset:\n")
print("red,green,blue,white,label")
for row in dataset:
    print(",".join(map(str, row)))

