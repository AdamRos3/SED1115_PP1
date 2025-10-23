from machine import UART, Pin, ADC, PWM
import time

test_button = Pin(22, Pin.IN, Pin.PULL_DOWN)
prev_state = 0

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
uart.init(bits=8, parity=None, stop=1) 

adc = ADC(Pin(27))
pwm = PWM(Pin(0), freq=2000) 

duty_cycle = 32768
desired_value = (duty_cycle / 65535) * 3.3

pwm.duty_u16(duty_cycle) 


while True:
    current_state = test_button.value()
        
    if (prev_state == 0 and current_state == 1):
        message = str(desired_value) + '\n'
        uart.write(message)

        time.sleep(0.3) # Debounce delay
    
    if uart.any():
        data = uart.read()
        if data:
            data = data.decode('utf-8').strip()
            average_pwm = (float(adc.read_u16()) / 65535) * 3.3
            diff = abs(float(data) - average_pwm)

            print("Desired: " + data)
            print("Actual: " + str(average_pwm))
            print("Difference: " + str(diff))
            print()



    prev_state = current_state

    time.sleep(0.1)