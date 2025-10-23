from machine import Pin, ADC, PWM
import time

test_button = Pin(22, Pin.IN, Pin.PULL_DOWN)
prev_state = 0

adc = ADC(Pin(27))
pwm = PWM(Pin(0), freq=2000) 

duty_cycle = 32768
desired_value = (duty_cycle / 65535) * 3.3

pwm.duty_u16(duty_cycle) 


while True:
    current_state = test_button.value()
    average_pwm = (float(adc.read_u16()) / 65535) * 3.3

    if (prev_state == 0 and current_state == 1):
        diff = abs(desired_value - average_pwm)

        print("Desired: " + str(desired_value))
        print("Actual: " + str(average_pwm))
        print("Difference: " + str(diff))
        print()


        time.sleep(0.3) # Debounce delay

    prev_state = current_state

    time.sleep(0.1)