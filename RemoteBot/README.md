# RemoteBot Controller + Vehicle

This project pairs two ESP32s to create a remote-controlled bot. One board acts
as a handheld transmitter with forward/reverse buttons and a steering
potentiometer while the other drives a motorized chassis with a steering servo.
Communication uses ESP-NOW so the link is fast and doesn't require a Wi-Fi
network.

## Hardware overview

### Remote controller
* **Forward button** on GPIO 12 (active-low)
* **Reverse button** on GPIO 14 (active-low)
* **Steering potentiometer** on GPIO 34 (0-3.3 V input range)

The controller can be powered from USB or a battery. Replace the `VEHICLE_MAC`
constant in `controller.py` with the MAC address printed by the vehicle on
boot.

### Vehicle
* **Motor 1** forward/reverse inputs on GPIO 13 / 12
* **Motor 2** forward/reverse inputs on GPIO 27 / 14
* **Motor encoder 1** channels on GPIO 32 / 39
* **Motor encoder 2** channels on GPIO 21 / 22
* **Steering servo** signal on GPIO 15 (50 Hz)
* **Status LED** on GPIO 2 indicates a healthy data link
* Encoder pulse totals are printed to the serial console once per second

The `CONTROLLER_MAC` constant in `vehicle.py` must be set to the controller's
MAC address. On startup the vehicle prints its own MAC to the serial console to
simplify pairing.

## Story prompt

Our bot is a miniature Mars rover named *Astra*. The handheld controller is the
mission command console, sending forward, reverse, and steering commands while a
potentiometer turns the rover's camera mast. The ESP-NOW link acts as the deep
space relay keeping mission control and Astra connected.
