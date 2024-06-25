import network
import asyncio
from pico.machine_control import handle_request, pid_loop

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
    response = handle_request(request)
    if response is None:
        response = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nInternal Server Error'.encode('utf-8')
    await writer.write(response)
    await writer.drain()  # Ensure all data is sent
    await writer.close()

async def main():
    server = await asyncio.start_server(serve_client, '0.0.0.0', 80)
    asyncio.create_task(pid_loop())  # Start the PID control loop
    await server.serve_forever()

asyncio.run(main())
