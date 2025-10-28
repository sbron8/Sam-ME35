from machine import Pin, PWM
import time

# Setup winch motor on D27 and D14
M1 = PWM(Pin(14), freq=10000, duty_u16=0)
M2 = PWM(Pin(27), freq=10000, duty_u16=0)

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

def launch_at_time(wind_time):
    """
    Launch with a specific wind time in seconds.
    """
    print(f"\n{'='*50}")
    print(f"MANUAL MODE: Wind time {wind_time}s")
    print(f"{'='*50}")
    
    # Step 1: Servo holds
    move_servo(SERVO_HOLD_POSITION)
    time.sleep(0.5)
    
    # Step 2: Wind the motor at full speed
    print("Winding...")
    wind_motor(speed=100)
    time.sleep(wind_time)
    stop_motor()
    time.sleep(0.3)
    
    # Step 3: LAUNCH!
    print("🚀 LAUNCH!")
    move_servo(SERVO_RELEASE_POSITION)
    time.sleep(0.5)
    
    # Step 4: Reset
    move_servo(SERVO_HOLD_POSITION)
    time.sleep(0.5)
    
    print("Launch complete! Ready for next launch.\n")

def launch_at_distance(distance_inches):
    """
    Launch ball at a specific distance in inches.
    Uses calibrated distance-to-wind-time mapping.
    """
    # YOUR CALIBRATION DATA - From actual measurements!
    distance_map = {
        15:   1.0,   # 7 inches → 1.0s wind time
        35:  1.5,   # 22 inches → 1.5s wind time
        52:  2.0,
        58:  2.34,# 41 inches → 2.0s wind time
        62:  2.5,
        64:  2.62,# 52 inches → 2.5s wind time
        67:  3.0,   # 67 inches → 3.0s wind time
        75:  3.5,
        77:  3.73,
        85:  4.0,   # 90 inches → 4.0s wind time
        86:  4.2,   # 91 inches (max) → 4.2s wind time
    }
    
    # Find closest distance in map or interpolate
    distances = sorted(distance_map.keys())
    
    # Check if distance is in range
    if distance_inches < distances[0]:
        print(f"Warning: {distance_inches}\" is below minimum range ({distances[0]}\")")
        print(f"Using minimum distance: {distances[0]}\"")
        distance_inches = distances[0]
    elif distance_inches > distances[-1]:
        print(f"Warning: {distance_inches}\" is above maximum range ({distances[-1]}\")")
        print(f"Using maximum distance: {distances[-1]}\"")
        distance_inches = distances[-1]
    
    # Get wind time (exact match or interpolate)
    if distance_inches in distance_map:
        wind_time = distance_map[distance_inches]
    else:
        # Quadratic interpolation (uses 3 nearest points for better accuracy)
        for i in range(len(distances)-1):
            if distances[i] <= distance_inches <= distances[i+1]:
                # Use 3 points for quadratic fit when possible
                if i > 0:
                    # Use points [i-1, i, i+1]
                    d0, d1, d2 = distances[i-1], distances[i], distances[i+1]
                    t0, t1, t2 = distance_map[d0], distance_map[d1], distance_map[d2]
                    
                    # Lagrange quadratic interpolation
                    x = distance_inches
                    L0 = ((x - d1) * (x - d2)) / ((d0 - d1) * (d0 - d2))
                    L1 = ((x - d0) * (x - d2)) / ((d1 - d0) * (d1 - d2))
                    L2 = ((x - d0) * (x - d1)) / ((d2 - d0) * (d2 - d1))
                    wind_time = t0 * L0 + t1 * L1 + t2 * L2
                elif i < len(distances)-2:
                    # Use points [i, i+1, i+2]
                    d0, d1, d2 = distances[i], distances[i+1], distances[i+2]
                    t0, t1, t2 = distance_map[d0], distance_map[d1], distance_map[d2]
                    
                    # Lagrange quadratic interpolation
                    x = distance_inches
                    L0 = ((x - d1) * (x - d2)) / ((d0 - d1) * (d0 - d2))
                    L1 = ((x - d0) * (x - d2)) / ((d1 - d0) * (d1 - d2))
                    L2 = ((x - d0) * (x - d1)) / ((d2 - d0) * (d2 - d1))
                    wind_time = t0 * L0 + t1 * L1 + t2 * L2
                else:
                    # Fall back to linear for endpoints
                    d1, d2 = distances[i], distances[i+1]
                    t1, t2 = distance_map[d1], distance_map[d2]
                    ratio = (distance_inches - d1) / (d2 - d1)
                    wind_time = t1 + (t2 - t1) * ratio
                break
    
    print(f"\n{'='*50}")
    print(f"TARGET: {distance_inches} inches")
    print(f"Wind time: {wind_time:.2f}s")
    print(f"{'='*50}")
    
    # Step 1: Servo holds
    move_servo(SERVO_HOLD_POSITION)
    time.sleep(0.5)
    
    # Step 2: Wind the motor at full speed
    print("Winding...")
    wind_motor(speed=100)
    time.sleep(wind_time)
    stop_motor()
    time.sleep(0.3)
    
    # Step 3: LAUNCH!
    print("🚀 LAUNCH!")
    move_servo(SERVO_RELEASE_POSITION)
    time.sleep(0.5)
    
    # Step 4: Reset
    move_servo(SERVO_HOLD_POSITION)
    time.sleep(0.5)
    
    print("Launch complete! Ready for next launch.\n")

# Initialize
move_servo(SERVO_HOLD_POSITION)
time.sleep(0.5)

print("\n" + "="*60)
print("CATAPULT LAUNCH SYSTEM")
print("="*60)
print("Enter target distance in inches (e.g., '45')")
print("OR enter wind time in seconds with 's' (e.g., '2.5s')")
print("Press Enter to launch immediately")
print("="*60 + "\n")

# Main loop
while True:
    try:
        # Get input from user
        user_input = input("Enter distance (inches) or time (e.g., 2.5s) or 'q' to quit: ")
        
        if user_input.lower() == 'q':
            print("Exiting...")
            break
        
        # Check if input ends with 's' for manual time mode
        if user_input.lower().endswith('s'):
            # Manual time mode
            wind_time = float(user_input[:-1])  # Remove 's' and convert to float
            
            if wind_time > 4.2:
                print(f"Warning: Wind time {wind_time}s exceeds maximum 4.2s")
                print("Using maximum: 4.2s")
                wind_time = 4.2
            elif wind_time < 0:
                print("Error: Wind time must be positive")
                continue
            
            launch_at_time(wind_time)
        else:
            # Distance mode
            target_distance = float(user_input)
            launch_at_distance(target_distance)
    
    except ValueError:
        print("Invalid input! Enter a number (e.g., 45) or time with 's' (e.g., 2.5s)")
    except KeyboardInterrupt:
        print("\nExiting...")
        break

stop_motor()
move_servo(SERVO_HOLD_POSITION)
print("Program stopped.")