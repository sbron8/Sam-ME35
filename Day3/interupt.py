# setting up irq
from machine import Pin
import time
button = Pin(35, Pin.IN)
def callback(p):
    print("button is pressed")

button.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler= callback)