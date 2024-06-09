import time
import RPi.GPIO as GPIO


class MySensor:
    def __init__(self):
        # Hier können die jeweiligen Eingangs-/Ausgangspins ausgewählt werden
        self.trigger_pin = 23
        self.echo_pin = 24
        # Pause zwischen den einzelnen Messungen in Sekunden
        self.sleeptime = 0.8

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trigger_pin, False)

        print("Ultrasoundsensor is being initialized...")
        time.sleep(2)  # Initialisierungspause für den Sensor

    def get_distance(self):
        try:
            while True:
                # Trigger the sensor
                GPIO.output(self.trigger_pin, True)
                time.sleep(0.0001)  # Erhöhung der Dauer des Trigger-Pulses
                GPIO.output(self.trigger_pin, False)

                # Debugging: Status des Echo-Pins überwachen
                start_time = time.time()
                while GPIO.input(self.echo_pin) == 0:
                    if time.time() - start_time > 1:
                        print("Echo pin stuck at 0")
                        break
                    on_time = time.time()
                    print("Echo pin went HIGH, recorded on_time")

                start_time = time.time()
                while GPIO.input(self.echo_pin) == 1:
                    if time.time() - start_time > 1:
                        print("Echo pin stuck at 1")
                        break
                    off_time = time.time()
                    print("Echo pin went LOW, recorded off_time")

                # Prüfen, ob on_time und off_time gesetzt wurden
                if 'on_time' in locals() and 'off_time' in locals():
                    # Calculate the difference of our measured times
                    period = off_time - on_time
                    # Calculate the distance based on our calculated time
                    distance = (period * 34300) / 2
                    print(f"Distance: {distance:.2f} cm")
                else:
                    print("Failed to read distance")

                print("----------------------")
                time.sleep(self.sleeptime)
        except KeyboardInterrupt:
            print("Quitting application...")
            GPIO.cleanup()


sensor = MySensor()
sensor.get_distance()
