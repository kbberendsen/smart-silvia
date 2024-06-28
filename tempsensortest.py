import time
import machine
import onewire
from ds18x20 import DS18X20

from machine import ADC

# Internal temperature sensor is connected to ADC channel 4
temp_sensor = ADC(4)

def read_internal_temperature():
    # Read the raw ADC value
    adc_value = temp_sensor.read_u16()

    # Convert ADC value to voltage
    voltage = adc_value * (3.3 / 65535.0)

    # Temperature calculation based on sensor characteristics
    temperature_celsius = 27 - (voltage - 0.706) / 0.001721

    return temperature_celsius

def celsius_to_fahrenheit(temp_celsius): 
    temp_fahrenheit = temp_celsius * (9/5) + 32 
    return temp_fahrenheit



# the device is on GPIO12
dat = machine.Pin(2)
power_pin = machine.Pin(3, machine.Pin.OUT)
power_pin.on()

# create the onewire object
ds = DS18X20(onewire.OneWire(dat))

# scan for devices on the bus
roms = ds.scan()
print('found devices:', roms)

# loop 10 times and print all temperatures
for i in range(1000):
    print('temperatures:', end=' ')
    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        print(ds.read_temp(rom), end=' ')
        
    # Reading and printing the internal temperature
    temperatureC = read_internal_temperature()
    print("Internal Temperature:", temperatureC, "°C")
    print()

