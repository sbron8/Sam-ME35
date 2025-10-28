from machine import Pin, PWM
import time

# Setup buttons on D34 and D35 (with internal pull-up resistors)
button_motor = Pin(34, Pin.IN, Pin.PULL_UP)
button_servo = Pin(35, Pin.IN, Pin.PULL_UP)

# Setup motor on D27 and D14
M1 = PWM(Pin(14), freq=1000, duty_u16=0)
M2 = PWM(Pin(27), freq=1000, duty_u16=0)

# Setup servo on Pin 19
servo = PWM(Pin(19), freq=50)

def stop_motor():
    M1.duty_u16(0)
    M2.duty_u16(0)

def start_motor_backward(speed=100):
    duty = int(speed * 65535 / 100)
    M1.duty_u16(0)
    M2.duty_u16(duty)

def angle_to_duty(angle):
    min_duty = 1638
    max_duty = 8192
    return int(min_duty + (max_duty - min_duty) * angle / 180)

def move_servo(angle):
    servo.duty_u16(angle_to_duty(angle))

# Set initial servo position (change this value to adjust starting position)
SERVO_START_POSITION = 160  # Change this to your desired starting angle (0-180)
SERVO_PRESSED_POSITION = 20  # Position when D35 is pressed

# Initialize servo to starting position
move_servo(SERVO_START_POSITION)
time.sleep(0.5)  # Give servo time to reach initial position

print("Ready! Hold D34 to move motor backward, press D35 to move servo")

# Main loop
while True:
    # Check if motor button (D34) is pressed - move motor backward
    if button_motor.value() == 0:
        start_motor_backward(speed=100)
    else:
        stop_motor()
    
    # Check if servo button (D35) is pressed - move servo to pressed position
    if button_servo.value() == 0:
        move_servo(SERVO_PRESSED_POSITION)
    else:
        move_servo(SERVO_START_POSITION)  # Return to starting position when released
    
    time.sleep(0.05)  # Small delay for responsive control

