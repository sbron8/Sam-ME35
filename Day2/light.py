import machine, neopixel
np = neopixel.NeoPixel(machine.Pin(15), 2)

np[0] = (255, 0, 0) # set to red, full brightness
np[1] = (255, 0, 255) # set to green, half brightness

np.write()