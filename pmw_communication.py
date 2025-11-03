# ads1x15.py must be loaded onto the pico
from machine import Pin, UART, I2C, PWM
from ads1x15 import ADS1015
from collections import deque 
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

# Queue for transmition data
transmitionQueue = deque((),10)

# Timekeepers for timeout (ms)
last_sent = None
last_received = None
TIMEOUT_THRESHOLD = 1000

i2c = I2C(1, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL))
adc = ADS1015(i2c, ADS1015_ADDR, 1)
pwm = PWM(Pin(PWM_GENERATOR), freq=10000) 

duty_cycle = 32768
my_desired_value = (duty_cycle / 65535) * 3.3

pwm.duty_u16(duty_cycle) 

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
uart.init(bits=8, parity=None, stop=1) 

def print_order(difference: float):
    #Prints the order relationship between desired and actual based on the difference value
    order = None
    if difference > 0:
        order = "Desired > Actual"
    elif difference < 0:
        order = "Desired < Actual"
    else:
        order = "Desired = Actual"

    print("\n" + order + "\n")

def print_difference_data(desired: float, actual: float, who: str):
    #Prints the desired, actual, and difference values with who the data belongs to
    difference = desired - actual

    print(who + " Desired: " + str(desired) + "V")
    print(who + " Actual: " + str(actual) + "V")
    print(who + " Difference: " + str(abs(difference)) + "V", end=" ")

    print_order(difference)    

def queue_transmissions(data: str):
    #Queues the data for transmition
    activeT_tag = False
    activeR_tag = False
    nextMessage = []
    for c in data:
        if c == "T":
            if activeR_tag == True or activeT_tag == True:
                transmitionQueue.append("".join(nextMessage))
                nextMessage = []
            activeT_tag = True
            activeR_tag = False
            nextMessage = [TRANSMIT_TAG]
        elif c == "R":
            if activeR_tag == True or activeT_tag == True:
                transmitionQueue.append("".join(nextMessage))
                nextMessage = []
            activeR_tag = True
            activeT_tag = False
            nextMessage = [RECEIVE_TAG]
        elif activeT_tag == True and c != "R":
            nextMessage.append(c)
        elif activeR_tag == True and c != "T":
            nextMessage.append(c)
    if activeR_tag == True or activeT_tag == True:
        transmitionQueue.append("".join(nextMessage))


            

def strip_tags(data: str, tag: str) -> float:
    #Returns the float value from a tagged message- with error checking, if the message is not formatted correctly
    message_insert = None
    if tag == TRANSMIT_TAG:
        message_insert = "desired"
    elif tag == RECEIVE_TAG:
        message_insert = "actual"
    else:
        print("Data invalidly tagged")
        print("Tag: " + tag)
        raise ValueError
    
    try:
        return float(data[1:])
    except ValueError as e:
        print("Invalid " + message_insert + " value received, terminating program...")
        print("Data: " + data + "\nError:", end=" ")
        raise
    except Exception as e:
        print("Something has gone very wrong with receiving a " + message_insert + " value, terminating program...")
        print("Data: " + data + "\nError:", end=" ")
        raise


def handle_receiving_desired(data):
    other_desired_value = strip_tags(data, TRANSMIT_TAG)

    other_actual_value = adc.raw_to_v(adc.read(0, ADS1015_PWM))
    received = RECEIVE_TAG + str(other_actual_value)
    uart.write(received.encode('utf-8'))

    print_difference_data(other_desired_value, other_actual_value, "Other")

def handle_receiving_actual(data):
    global last_received
    
    my_actual_value = strip_tags(data, RECEIVE_TAG)
    last_received = (time.time() * 1000)

    print_difference_data(my_desired_value, my_actual_value, "My")


while True:
    try:
        #current_time = (time.time() * 1000)

        # time() returns seconds since the Epoch so multiply by 1000 to convert to ms
        if last_sent and last_received:
            if (last_received - last_sent) > TIMEOUT_THRESHOLD:
                print("Connection timeout...")
                break
        elif not last_received and not last_sent:
            print("Here")

        transmition = TRANSMIT_TAG + str(my_desired_value)
        #Mark the start of transmission with a T- to let other pico know this is a desired value
        last_sent = (time.time() * 1000)
        
        uart.write(transmition.encode('utf-8'))
        #Write the desired value to the UART buffer marked with the transmit tag

        if uart.any():
            #If anything in the buffer read it
            data = uart.read()

            if data:
                data = data.decode('utf-8').strip()
                #Get whatever data was read and decode it to a string
                queue_transmissions(data)
            
            if len(transmitionQueue) > 0:
                #If there is anything in the queue process it
                nextMessage = transmitionQueue.popleft()
                print(nextMessage)
                if nextMessage.startswith(TRANSMIT_TAG):
                    handle_receiving_desired(nextMessage)
                elif nextMessage.startswith(RECEIVE_TAG):
                    handle_receiving_actual(nextMessage)
                else:
                    print("Message in queue invalidly tagged, skipping...")
                    raise ValueError

        time.sleep(0.5)
    except Exception as e:
        print(e)
        break

print("program terminated")


#TODO Possibly implement way to change PWM duty cycle without stoping and changing value in program
#TODO Impletent restart program