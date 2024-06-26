import network
import asyncio
from machine_control import handle_request, pid_loop

# <canvas id="tempChart" width="400" height="200"></canvas>

# HTML content with external CSS and JS from GitHub
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Smart Silvia</title>
    <link rel="stylesheet" href="https://kbberendsen.github.io/smart-silvia/frontend/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://kbberendsen.github.io/smart-silvia/frontend/script.js"></script>
</head>
<body>
    <h1>Smart Silvia</h1>
    <div id="statusMessage">
        <span id="statusDot" class="status-dot"></span>
        <span id="statusText" class="status-text">Status: Loading...</span>
    </div>
    <div id="currentTemp">
        Current Temperature: <span id="temperature">0</span>°C
        <span id="tempStatusDot" class="status-dot orange-dot"></span>
    </div>
    <div id="targetTemp">Target Temperature: <span id="targetTemperature">0</span>°C</div>
    <div id="tempSetContainer" style="display: flex; flex-direction: column; align-items: center;">
        <input type="number" id="tempInput" min="90" max="98" placeholder="Set target temp" required style="margin-bottom: 10px;">
        <button onclick="setTemperature()">Set Temperature</button>
    </div>
    
</body>
</html>
"""

# Connect to Wi-Fi
# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect('your-SSID', 'your-PASSWORD')

# while not wlan.isconnected():
#     pass

# print('network config:', wlan.ifconfig())

# Serve Web Application
async def serve_client(reader, writer):
    request = await reader.read(1024)
    request = request.decode('utf-8')  # Decode the request to string
    print("Request:", request)  # Debugging line

    # Handle the request
    response = handle_request(request)
    if response is None:
        # If handle_request returns None, serve the HTML page for root or return 404
        if request.startswith('GET / ') or request.startswith('GET /index.html '):
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{}'.format(html).encode('utf-8')
        else:
            response = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nNot Found'.encode('utf-8')
    
    await writer.write(response)
    await writer.drain()  # Ensure all data is sent
    await writer.close()

async def main():
    server = await asyncio.start_server(serve_client, '0.0.0.0', 80)
    asyncio.create_task(pid_loop())  # Start the PID control loop
    await server.serve_forever()

asyncio.run(main())
