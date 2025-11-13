# sensor.py
# HC-SR04 ultrasonic sensor abstraction with RPi.GPIO fallback to simulator.
import time
import random
from config import BIN_HEIGHT_CM_DEFAULT

try:
    import RPi.GPIO as GPIO
    IS_RPI = True
except Exception:
    IS_RPI = False

class UltrasonicSensor:
    """
    HC-SR04 driver abstraction.
    If running on non-RPi environment, get_distance_cm() returns simulated values.
    """
    def __init__(self, trig_pin=23, echo_pin=24, max_distance_cm=None):
        self.trig = trig_pin
        self.echo = echo_pin
        self.max_distance_cm = max_distance_cm or BIN_HEIGHT_CM_DEFAULT

        if IS_RPI:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trig, GPIO.OUT)
            GPIO.setup(self.echo, GPIO.IN)
            GPIO.output(self.trig, False)
            time.sleep(0.5)

    def get_distance_cm(self):
        """Return measured distance in cm; simulation when not on RPi."""
        if not IS_RPI:
            # simulate noise and plausible range: 2 cm to max_distance
            return max(2.0, min(self.max_distance_cm, random.gauss(self.max_distance_cm * 0.5, self.max_distance_cm*0.15)))

        # real hardware reading
        GPIO.output(self.trig, True)
        time.sleep(0.00001)  # 10us
        GPIO.output(self.trig, False)

        pulse_start = time.time()
        timeout = pulse_start + 0.04

        while GPIO.input(self.echo) == 0 and time.time() < timeout:
            pulse_start = time.time()

        pulse_end = time.time()
        while GPIO.input(self.echo) == 1 and time.time() < timeout:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        # distance in cm
        distance_cm = (pulse_duration * 34300.0) / 2.0
        if distance_cm <= 0 or distance_cm > 400:
            return float(self.max_distance_cm)
        return min(distance_cm, float(self.max_distance_cm))

    def get_fill_level_percent(self, bin_height_cm):
        """
        Convert distance reading to fill %:
            0% -> empty (distance == bin_height_cm)
            100% -> full (distance near 0)
        """
        dist = self.get_distance_cm()
        effective = min(dist, bin_height_cm)
        fill = (1.0 - (effective / float(bin_height_cm))) * 100.0
        fill = max(0.0, min(100.0, fill))
        return round(fill, 1)

    def cleanup(self):
        if IS_RPI:
            GPIO.cleanup()
