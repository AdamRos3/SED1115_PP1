from machine import UART, Pin, ADC
import time

test_button = Pin(22, Pin.IN, Pin.PULL_DOWN)
prev_state = 0

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
uart.init(bits=8, parity=None, stop=1) 

adc = ADC(Pin(28))

while True:
    current_state = test_button.value()
        
    if (prev_state == 0 and current_state == 1):
        uart.write('27\n')

        time.sleep(0.3) # Debounce delay
    
    if uart.any():
        data = uart.read()
        if data:
            print(data.decode('uft-8').strip())

    prev_state = current_state

    time.sleep(0.1)