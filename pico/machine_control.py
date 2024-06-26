import json
import asyncio
from lib.pid import PID

# Initialize PID controllers
coffee_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=93)
steam_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=140)

current_temperature = 20
mode = 'coffee'

def handle_request(request):
    global coffee_pid, steam_pid, current_temperature, mode

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
    global current_temperature, mode
    while True:
        current_temperature += 1  # Simulate sensor reading
        pid_output = (coffee_pid if mode == 'coffee' else steam_pid).compute(current_temperature)
        await asyncio.sleep(1)

pid_loop = update_pid
