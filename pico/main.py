import network
import asyncio
from time import sleep
from machine_control import handle_request, pid_loop
from machine import Pin, I2C
from secrets import WIFI_SSD, WIFI_PASSWORD
import lib.ssd1306 as ssd1306

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
        <input type="number" id="tempInput" min="90" max="98" placeholder="Target temp" required style="margin-bottom: 10px;">
        <button onclick="setTemperature()">Set Temperature</button>
    </div>
    
</body>
</html>
"""

wlan = network.WLAN(network.STA_IF)
# Connect to Wi-Fi
if not wlan.isconnected():
    wlan.active(True)
    wlan.connect(WIFI_SSD, WIFI_PASSWORD)

while not wlan.isconnected():
    print('Connecting...')
    sleep(1)
    pass

print('Network config:', wlan.ifconfig())

wlan_ip = wlan.ifconfig()[0]
print(wlan_ip)

# Display
i2c = I2C(0, sda=Pin(16), scl=Pin(17))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

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
    
    writer.write(response)
    await writer.drain()  # Ensure all data is sent
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(serve_client, '0.0.0.0', 80)

    # Display IP on startup
    display.fill(0)
    display.text('IP Address', 15, 24, 1)
    display.text(f'{wlan_ip}', 15, 33, 1)
    display.show()
    sleep(5)

    asyncio.create_task(pid_loop())  # Start the PID control loop
    while True:
        await asyncio.sleep(0.1)

asyncio.run(main())
