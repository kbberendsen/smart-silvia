import json
import asyncio
from lib.pid import PID
import onewire
import machine
from ds18x20 import DS18X20
from machine import Pin, I2C
import ssd1306

# using default address 0x3C
i2c = I2C(0, sda=Pin(16), scl=Pin(17))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# P: if you’re not where you want to be, get there.
# I: if you haven’t been where you want to be for a long time, get there faster
# D: if you’re getting close to where you want to be, slow down.

# Initialize PID controllers
coffee_pid = PID(Kp=45, Ki=0.1, Kd=0.05, setpoint=94.00)
steam_pid = PID(Kp=45, Ki=0.1, Kd=0.05, setpoint=140.00)

mode = 'coffee'

# Temp device is on GPIO12
dat = machine.Pin(2)
power_pin = machine.Pin(3, machine.Pin.OUT)
power_pin.on()

# Create the onewire object (temp)
ds = DS18X20(onewire.OneWire(dat))

# Display
i2c = I2C(0, sda=Pin(16), scl=Pin(17))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

target_temp = coffee_pid.setpoint if mode == 'coffee' else steam_pid.setpoint

def handle_request(request):
    global coffee_pid, steam_pid, current_temperature, target_temp, mode

    print("Request received:", request)  # Debugging line

    try:
        method, path, version = request.split(' ', 2)
    except ValueError:
        return 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nInvalid request format'.encode('utf-8')

    # GET current temperature
    if path == '/temperature':
        if method == 'GET':
            return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{current_temperature}'.encode('utf-8')

    # GET target temperature
    elif path == '/targetTemperature':
        if method == 'GET':
            target_temp = coffee_pid.setpoint if mode == 'coffee' else steam_pid.setpoint
            return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{target_temp}'.encode('utf-8')

    # POST coffee or steam mode
    elif path == '/mode':
        if method == 'POST':
            content_length = int(request.split('Content-Length: ')[1].split('\r\n')[0])
            body = request.split('\r\n\r\n')[1][:content_length]
            new_mode = body.split('mode=')[1]
            if new_mode in ['coffee', 'steam']:
                mode = new_mode
                return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{mode}'.encode('utf-8')
            else:
                return 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nInvalid mode'.encode('utf-8')
            
    # POST set temperature
    elif path == '/setTemperature':
        if method == 'POST':
            content_length = int(request.split('Content-Length: ')[1].split('\r\n')[0])
            body = request.split('\r\n\r\n')[1][:content_length]
            params = dict(x.split('=') for x in body.split('&'))
            temperature = float(params.get('temperature', 0))

            # Validate and set temperature
            if 90 <= temperature <= 98:
                if mode == 'coffee':
                    coffee_pid.setpoint = temperature
                else:
                    steam_pid.setpoint = temperature
                return 'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nTemperature set successfully'.encode('utf-8')
            else:
                return 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nTemperature out of range'.encode('utf-8')

    # GET intitial data (current temp, target temp, mode)
    elif path == '/initialData':
        if method == 'GET':
            target_temp = coffee_pid.setpoint if mode == 'coffee' else steam_pid.setpoint
            initial_data = {
                'currentTemperature': current_temperature,
                'targetTemperature': target_temp,
                'mode': mode
            }
            return f'HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n{json.dumps(initial_data)}'.encode('utf-8')
    
    # If the path is not recognized, return None
    return None

async def update_pid():
    global current_temperature, target_temp, mode
    # scan for devices on the bus
    roms = ds.scan()
    while True:
        ds.convert_temp()
        current_temperature = round(ds.read_temp(roms[0]), 2)
        pid_output = (coffee_pid if mode == 'coffee' else steam_pid).compute(current_temperature)
        display.fill(0)
        display.text(f'Temp:   {current_temperature}', 15, 24, 1)
        display.text(f'Target: {round(target_temp, 2)}', 15, 33, 1)
        display.show()

        await asyncio.sleep(1)

pid_loop = update_pid
