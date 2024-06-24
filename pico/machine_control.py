import machine
import uasyncio as asyncio
from lib.pid import PID

# Initialize control pins and sensors
relay = machine.Pin(5, machine.Pin.OUT)
sensor = machine.ADC(0)  # Replace with your actual sensor

# PID controller settings for coffee and steam
coffee_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=90)  # Example values, adjust as needed
steam_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=130)  # Example values, adjust as needed

current_temperature = 0
mode = 'coffee'  # Default mode

# Function to handle HTTP requests
def handle_request(request):
    global coffee_pid, steam_pid, current_temperature, mode

    if request.startswith(b'GET /on'):
        relay.value(1)
        return 'HTTP/1.1 200 OK\r\n\r\nOn'
    
    elif request.startswith(b'GET /off'):
        relay.value(0)
        return 'HTTP/1.1 200 OK\r\n\r\nOff'
    
    elif request.startswith(b'GET /temperature'):
        return f'HTTP/1.1 200 OK\r\n\r\n{current_temperature}'
    
    elif request.startswith(b'GET /targetTemperature'):
        if mode == 'coffee':
            target_temp = coffee_pid.setpoint
        else:
            target_temp = steam_pid.setpoint
        return f'HTTP/1.1 200 OK\r\n\r\n{target_temp}'
    
    elif request.startswith(b'POST /setpoint'):
        setpoint = float(request.split(b'setpoint=')[1])
        if mode == 'coffee':
            coffee_pid.setpoint = setpoint
        else:
            steam_pid.setpoint = setpoint
        return f'HTTP/1.1 200 OK\r\n\r\n{setpoint}'
    
    elif request.startswith(b'POST /mode'):
        new_mode = request.split(b'mode=')[1].decode()
        if new_mode in ['coffee', 'steam']:
            mode = new_mode
            return f'HTTP/1.1 200 OK\r\n\r\n{mode}'
        else:
            return 'HTTP/1.1 400 Bad Request\r\n\r\nInvalid mode'
    
    elif request.startswith(b'GET '):
        path = request.split(b' ')[1].decode()
        if path == '/':
            path = '/index.html'
        try:
            with open('frontend' + path, 'r') as f:
                if path.endswith('.html'):
                    content_type = 'text/html'
                elif path.endswith('.css'):
                    content_type = 'text/css'
                elif path.endswith('.js'):
                    content_type = 'application/javascript'
                else:
                    content_type = 'text/plain'
                return f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n' + f.read()
        except Exception as e:
            return 'HTTP/1.1 404 Not Found\r\n\r\nFile not found'
    
    else:
        return 'HTTP/1.1 400 Bad Request\r\n\r\nInvalid request'

# Function to update the PID controller
async def update_pid():
    global current_temperature, mode
    while True:
        current_temperature = sensor.read()  # Read the temperature sensor
        pid_output = (coffee_pid if mode == 'coffee' else steam_pid).compute(current_temperature)
        relay.value(1 if pid_output > 0 else 0)
        await asyncio.sleep(1)

# Expose the PID loop for running in main.py
pid_loop = update_pid
