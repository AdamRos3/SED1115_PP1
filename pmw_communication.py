# ads1x15.py must be loaded onto the pico
from machine import Pin, UART, I2C, PWM
from ads1x15 import ADS1015
import time


# I2C signal pins
I2C_SDA = 14
I2C_SCL = 15

# PWM generating pin
PWM_GENERATOR = 0

# ADS 1015 configuration information
ADS1015_ADDR = 0x48
ADS1015_PWM = 2     # port 2 has (low-pass filtered) PWM signal

# Communication tags
TRANSMIT_TAG = "T"
RECEIVE_TAG = "R"


i2c = I2C(1, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL))
adc = ADS1015(i2c, ADS1015_ADDR, 1)
pwm = PWM(Pin(PWM_GENERATOR), freq=10000) 

duty_cycle = 32768
my_desired_value = (duty_cycle / 65535) * 3.3

pwm.duty_u16(duty_cycle) 

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
uart.init(bits=8, parity=None, stop=1) 

def print_order(difference: float):
    order = None
    if difference > 0:
        order = "Desired > Actual"
    elif difference < 0:
        order = "Desired < Actual"
    else:
        order = "Desired = Actual"

    print(order + "\n")

def print_difference_data(desired: float, actual: float, who: str):
    difference = desired - actual

    print(who + " Desired: " + str(desired) + "V")
    print(who + " Actual: " + str(actual) + "V")
    print(who + " Difference: " + str(abs(difference)) + "V", end=" ")

    print_order(difference)    

def strip_tags(data: str, tag: str) -> float:
    message_insert = None
    if tag == TRANSMIT_TAG:
        message_insert = "desired"
    elif tag == RECEIVE_TAG:
        message_insert = "actual"
    else:
        return -1
    
    try:
        return float(data[1:0])
    except ValueError:
        print("Invalid " + message_insert + " value received, terminating program...")
    except Exception as e:
        print("Something has gone very wrong with receiving a " + message_insert + " value, terminating program...")
        print(e)
    finally:
        return -1

while True:
    transmition = TRANSMIT_TAG + str(my_desired_value)
    
    uart.write(transmition.encode('utf-8'))

    if uart.any():
        data = uart.read()

        if data:
            data = data.decode('utf-8').strip()

            if data.startswith(TRANSMIT_TAG):
                other_desired_value = strip_tags(data, TRANSMIT_TAG)
                if other_desired_value == -1: break

                other_actual_value = adc.raw_to_v(adc.read(0, ADS1015_PWM))
                received = RECEIVE_TAG + str(other_actual_value)
                uart.write(received.encode('utf-8'))

                print_difference_data(other_desired_value, other_actual_value, "Other")

            elif data.startswith(RECEIVE_TAG):
                my_actual_value = strip_tags(data, RECEIVE_TAG)
                if my_actual_value == -1: break

                print_difference_data(my_desired_value, my_actual_value, "My")
            else:
                print("Invalid message received; no valid tag exists, terminating program...")
                break

    time.sleep(0.5)

print("program terminated")


#TODO Timeout when resposes not recieved
#TODO Possibly implement way to change PWM duty cycle without stoping and changing value in program