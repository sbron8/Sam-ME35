from machine import Pin, PWM
import time

# Setup buttons
button_launch = Pin(34, Pin.IN, Pin.PULL_UP)

# Setup winch motor on D27 and D14
M1 = PWM(Pin(14), freq=8000, duty_u16=0)
M2 = PWM(Pin(27), freq=8000, duty_u16=0)

# Setup servo on Pin 19 (release mechanism)
servo = PWM(Pin(19), freq=50)

# Servo positions
SERVO_HOLD_POSITION = 125
SERVO_RELEASE_POSITION = 20

def stop_motor():
    M1.duty_u16(0)
    M2.duty_u16(0)

def wind_motor(speed=100):
    duty = int(speed * 65535 / 100)
    M1.duty_u16(0)
    M2.duty_u16(duty)

def angle_to_duty(angle):
    min_duty = 1638
    max_duty = 8192
    return int(min_duty + (max_duty - min_duty) * angle / 180)

def move_servo(angle):
    servo.duty_u16(angle_to_duty(angle))

def test_launch(wind_time):
    """Launch with a specific wind time"""
    print(f"\n{'='*50}")
    print(f"TESTING WIND TIME: {wind_time} seconds")
    print(f"{'='*50}")
    
    # Step 1: Servo holds
    move_servo(SERVO_HOLD_POSITION)
    time.sleep(0.5)
    
    # Step 2: Wind the motor
    print(f"Winding for {wind_time}s...")
    wind_motor(speed=100)
    time.sleep(wind_time)
    stop_motor()
    time.sleep(0.3)
    
    # Step 3: Release!
    print("LAUNCH!")
    move_servo(SERVO_RELEASE_POSITION)
    time.sleep(0.5)
    
    # Step 4: Reset
    move_servo(SERVO_HOLD_POSITION)
    time.sleep(0.5)
    
    print("Launch complete!")

# Initialize
move_servo(SERVO_HOLD_POSITION)
time.sleep(0.5)

print("\n" + "="*60)
print("CATAPULT CALIBRATION TOOL")
print("="*60)
print("\nThis tool will test different wind times.")
print("For each launch:")
print("  1. Press D34 to launch")
print("  2. Measure the distance in inches")
print("  3. Write down: wind_time -> distance")
print("\nYou'll manually reset the catapult between launches.")
print("="*60)

# Wind times to test (in seconds)
# Adjust these based on your motor speed
# Max wind time is 4.2 seconds
wind_times_to_test = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.2]

current_test = 0
total_tests = len(wind_times_to_test)

print(f"\nReady to test {total_tests} different wind times")
print(f"Wind times: {wind_times_to_test}")
print("\nPress D34 when ready for first launch...")

# Store calibration results
calibration_data = []

while current_test < total_tests:
    if button_launch.value() == 0:
        wind_time = wind_times_to_test[current_test]
        
        # Launch
        test_launch(wind_time)
        
        print(f"\n>>> MEASURE THE DISTANCE NOW <<<")
        print(f"Wind time: {wind_time}s")
        print(f"Progress: {current_test + 1}/{total_tests}")
        
        # Get distance input from user
        distance_str = input("Enter distance in inches: ")
        try:
            distance = float(distance_str)
            calibration_data.append((distance, wind_time))
            print(f"Recorded: {distance} inches at {wind_time}s wind time")
        except:
            print("Invalid input! Please enter a number.")
            print("This test will be skipped.")
        
        current_test += 1
        
        if current_test < total_tests:
            print(f"\nNext test: {wind_times_to_test[current_test]}s")
            print("Reset your catapult, then press D34 for next launch...")
        else:
            print("\n" + "="*60)
            print("CALIBRATION COMPLETE!")
            print("="*60)
            print("\nYour calibration data:")
            print("distance_map = {")
            for distance, wt in sorted(calibration_data):
                print(f"    {int(distance)}:  ({wt}, 100),   # {distance} inches")
            print("}")
            print("\nCopy this into your main launch code!")
        
        # Wait for button release
        while button_launch.value() == 0:
            time.sleep(0.1)
        
        time.sleep(0.5)
    
    time.sleep(0.05)

# After all tests complete, just idle
print("\nCalibration tool finished. Reset ESP32 to run again.")
while True:
    time.sleep(1)