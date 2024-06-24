import asyncio
from lib.pid import PID

# PID controller settings for coffee and steam
coffee_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=93)  # Example values, adjust as needed
steam_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=140)  # Example values, adjust as needed

current_temperature = 0
mode = 'coffee'  # Default mode

import os
import json

# Function to hanlde HTTP requests
import os
import json

def handle_request(request):
    global coffee_pid, steam_pid, current_temperature, mode

    if request.startswith(b'GET /temperature'):
        if current_temperature is None:
            return 'HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nNo temperature reading available'.encode('utf-8')
        return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{current_temperature}'.encode('utf-8')
    
    elif request.startswith(b'GET /targetTemperature'):
        if mode == 'coffee':
            target_temp = coffee_pid.setpoint
        else:
            target_temp = steam_pid.setpoint
        return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{target_temp}'.encode('utf-8')
    
    elif request.startswith(b'POST /setpoint'):
        content_length = int(request.split(b'Content-Length: ')[1].split(b'\r\n')[0])
        body = request.split(b'\r\n\r\n')[1][:content_length]
        setpoint = float(body.split(b'setpoint=')[1])
        if mode == 'coffee':
            coffee_pid.setpoint = setpoint
        else:
            steam_pid.setpoint = setpoint
        return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{setpoint}'.encode('utf-8')
    
    elif request.startswith(b'POST /mode'):
        content_length = int(request.split(b'Content-Length: ')[1].split(b'\r\n')[0])
        body = request.split(b'\r\n\r\n')[1][:content_length]
        new_mode = body.split(b'mode=')[1].decode()
        if new_mode in ['coffee', 'steam']:
            mode = new_mode
            return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{mode}'.encode('utf-8')
        else:
            return 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nInvalid mode'.encode('utf-8')
    
    elif request.startswith(b'GET /initialData'):
        if mode == 'coffee':
            target_temp = coffee_pid.setpoint
        else:
            target_temp = steam_pid.setpoint
        initial_data = {
            'currentTemperature': current_temperature if current_temperature is not None else 'N/A',
            'targetTemperature': target_temp,
            'mode': mode
        }
        return f'HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n{json.dumps(initial_data)}'.encode('utf-8')
    
    # Serve default web page and static files
    elif request.startswith(b'GET '):
        path = request.split(b' ')[1].decode()
        if path == '/':
            path = '/index.html'
        full_path = os.path.join(os.path.dirname(__file__), '../frontend' + path)
        print(f"Trying to serve file: {full_path}")  # Debugging print statement
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if path.endswith('.html'):
                    content_type = 'text/html; charset=utf-8'
                elif path.endswith('.css'):
                    content_type = 'text/css; charset=utf-8'
                elif path.endswith('.js'):
                    content_type = 'application/javascript; charset=utf-8'
                else:
                    content_type = 'text/plain; charset=utf-8'
                response_body = f.read()
                return (f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n' + response_body).encode('utf-8')
        except Exception as e:
            print(f"Error serving file: {e}")  # Debugging print statement
            return 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nFile not found'.encode('utf-8')
    
    else:
        return 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nInvalid request'.encode('utf-8')



# Function to update the PID controller
async def update_pid():
    global current_temperature, mode
    while True:
        current_temperature += 1  # Simulate sensor reading
        pid_output = (coffee_pid if mode == 'coffee' else steam_pid).compute(current_temperature)
        #relay.value(1 if pid_output > 0 else 0)
        await asyncio.sleep(1)

# Expose the PID loop for running in main.py
pid_loop = update_pid
