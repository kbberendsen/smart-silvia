import os
import json
import asyncio
from lib.pid import PID

coffee_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=93)
steam_pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=140)

current_temperature = 20
mode = 'coffee'

def handle_request(request):
    global coffee_pid, steam_pid, current_temperature, mode

    if request.startswith(b'GET /temperature'):
        return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{current_temperature}'.encode('utf-8')
    
    elif request.startswith(b'GET /targetTemperature'):
        target_temp = coffee_pid.setpoint if mode == 'coffee' else steam_pid.setpoint
        return f'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{target_temp}'.encode('utf-8')

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
        target_temp = coffee_pid.setpoint if mode == 'coffee' else steam_pid.setpoint
        initial_data = {
            'currentTemperature': current_temperature,
            'targetTemperature': target_temp,
            'mode': mode
        }
        return f'HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n{json.dumps(initial_data)}'.encode('utf-8')
    
    elif request.startswith(b'GET '):
        path = request.split(b' ')[1].decode()
        if path == '/':
            path = '/index.html'
        full_path = os.path.join(os.path.dirname(__file__), '../frontend' + path)
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
            return 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nFile not found'.encode('utf-8')

    else:
        return 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nInvalid request'.encode('utf-8')

async def update_pid():
    global current_temperature, mode
    while True:
        current_temperature += 1  # Simulate sensor reading
        pid_output = (coffee_pid if mode == 'coffee' else steam_pid).compute(current_temperature)
        await asyncio.sleep(1)

pid_loop = update_pid
