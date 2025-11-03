# Note: for this to properly be imported, the ads1x15.py file must be loaded onto the pico
from ads1x15 import ADS1015
from machine import Pin, ADC, PWM, I2C
import time

# I2C signal pins
I2C_SDA = 14
I2C_SCL = 15

# PWM generating pin
PWM_GENERATOR = 0

# ADS 1015 configuration information
ADS1015_ADDR = 0x48
ADS1015_PWM = 2     # port 2 has (low-pass filtered) PWM signal

i2c = I2C(1, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL))
adc = ADS1015(i2c, ADS1015_ADDR, 1)
pwm = PWM(Pin(PWM_GENERATOR), freq=10000) 
potentiometer = ADC(Pin(27))

duty_cycle = 32768
desired_value = (duty_cycle / 65535) * 3.3

pwm.duty_u16(duty_cycle) 

while True:
    duty_cycle = potentiometer.read_u16()
    pwm.duty_u16(duty_cycle)
    desired_value = (duty_cycle / 65535) * 3.3
    average_pwm = adc.raw_to_v(adc.read(0, ADS1015_PWM))

    diff = abs(desired_value - average_pwm)

    print("Desired: " + str(desired_value) + "V")
    print("Actual: " + str(average_pwm) + "V")
    print("Difference: " + str(diff) + "V")
    print()

    time.sleep(1)