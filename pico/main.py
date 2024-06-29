import network
import urequests as requests
import uasyncio as asyncio
from time import sleep
from machine_control import handle_request, pid_loop
from machine import Pin, I2C
from secrets import WIFI_SSID, WIFI_PASSWORD
import lib.ssd1306 as ssd1306

# HTML content with external CSS and JS from GitHub
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Smart Silvia</title>
    <link rel="icon" href="https://kbberendsen.github.io/smart-silvia/frontend/favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://kbberendsen.github.io/smart-silvia/frontend/script.js"></script>
    <style>
        .status-dot {
            width: 1rem;
            height: 1rem;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.625rem;
            vertical-align: middle;
        }

        .green-dot {
            background-color: green;
        }

        .red-dot {
            background-color: red;
        }

        .orange-dot {
            background-color: orange;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-between min-h-screen bg-gray-200 text-center">
    <div class="flex flex-col items-center justify-center w-full h-1/3">
        <h1 class="text-black font-bold p-6 text-5xl sm:text-4xl md:text-5xl mb-5">Smart Silvia</h1>
        <div id="statusMessage" class="my-2 text-3xl sm:text-3xl md:text-2xl">
            <span id="statusDot" class="status-dot green-dot"></span>
            <span id="statusText">Online</span>
        </div>
        <div id="currentTemp" class="text-4xl sm:text-3xl md:text-4xl my-2">
            Current Temperature: <span id="temperature">28.88</span>°C
            <span id="tempStatusDot" class="status-dot orange-dot"></span>
        </div>
        <div id="targetTemp" class="text-4xl sm:text-3xl md:text-4xl my-2">
            Target Temperature: <span id="targetTemperature">98</span>°C
        </div>
        <div id="tempSetContainer" class="flex flex-col items-center mt-4 mb-6">
            <input type="number" id="tempInput" min="90" max="98" placeholder="Target temp" required class="mb-4 p-3 text-3xl sm:text-2xl border border-gray-300 rounded text-center w-full max-w-xs md:max-w-sm lg:max-w-md">
            <button onclick="setTemperature()" class="py-3 px-3 bg-gray-300 text-black rounded hover:bg-gray-400 text-3xl sm:text-2xl">Set Temperature</button>
        </div>
    </div>
    <div class="w-full h-2/3 flex-grow flex flex-col items-center pt-5">
        <div id="tempChart" class="w-4/5 h-full"></div>
    </div>
</body>
</html>

"""

# Display
i2c = I2C(0, sda=Pin(16), scl=Pin(17))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# Connect to Wi-Fi
display.fill(0)
display.text('Connecting...', 15, 24, 1)
display.show()

sleep(1)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

max_attempts = 15
attempts = 0
while not wlan.isconnected() and attempts < max_attempts:
    print(f'Attempt {attempts + 1} to connect to Wi-Fi...')
    display.fill(0)
    display.text('Connecting...', 15, 24, 1)
    display.text(f'Attempt {attempts + 1}', 15, 33, 1)
    display.show()
    sleep(1)
    attempts += 1

if wlan.isconnected():
    print('Successfully connected to Wi-Fi!')
    print('Network config:', wlan.ifconfig())
    wlan_ip = wlan.ifconfig()[0]
else:
    wlan_ip = None
    print('Failed to connect to Wi-Fi.')
    display.fill(0)
    display.text('Connection', 15, 24, 1)
    display.text('failed', 15, 33, 1)
    display.show()

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

    # # Display IP on startup
    display.fill(0)
    display.text('IP Address', 15, 24, 1)
    display.text(f'{wlan_ip}', 15, 33, 1)
    display.show()
    sleep(5)

    asyncio.create_task(pid_loop())  # Start the PID control loop
    while True:
        await asyncio.sleep(0.1)

asyncio.run(main())