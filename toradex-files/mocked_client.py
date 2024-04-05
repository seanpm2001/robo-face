import mmap
import os
import struct
import asyncio
import json
import websockets
import argparse  # Import the argparse module

def parse_arguments():
    parser = argparse.ArgumentParser(description='WebSocket server for robot control.')
    parser.add_argument('--remoteaddress', type=str, default='ws://0.0.0.0:8001', help='Server address for the Remote control in the format ws://ip:port')
    parser.add_argument('--uiaddress', type=str, default='ws://0.0.0.0:8000', help='Server address for the UI in the format ws://ip:port')
    return parser.parse_args()

async def receive_and_process_control(websocket, server_url):
    async for message in websocket:
        control_data = json.loads(message)
        print(f"Received control instructions from {server_url}: ", control_data)
        # Process control instructions...
async def send_telemetry(websocket):
    while True:
        telemetry_data = {
            "position": 1.234,
            "velocity": 0.123,
            "rotation": -0.004,
            "acceleration": 1.234,
            "cg_angle": 0.100,
            "cg_angular_velocity": -0.500,
            "battery": 11.1,
            "motor_amps": 0.4,
            "rawdata": {
                "accel": {
                    "x": 123.45,
                    "y": 456.78,
                    "z": 789.01
                },
                "gyro": {
                    "x": 123.45,
                    "y": 456.78,
                    "z": 789.01
                },
                "enc_left": {
                    "position": 12.3,
                    "velocity": 0.125
                },
                "enc_right": {
                    "position": 12.3,
                    "velocity": 0.121
                },
                "adc_battery": {
                    "voltage": 3.8
                },
                "adc_motor_left": {
                    "voltage": 1.2
                },
                "adc_motor_right": {
                    "voltage": 1.2
                }
            }
        }
        await websocket.send(json.dumps(telemetry_data))
        await asyncio.sleep(1)  # Adjust the frequency of telemetry updates as needed

async def manage_connection(server_url):
    while True:
        try:
            async with websockets.connect(server_url) as websocket:
                telemetry_task = asyncio.create_task(send_telemetry(websocket))
                control_task = asyncio.create_task(receive_and_process_control(websocket, server_url))  # Modified to include server_url
                await asyncio.gather(telemetry_task, control_task)
        except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK, ConnectionRefusedError, OSError) as e:
            print(f"Connection lost or cannot connect to {server_url}, attempting to reconnect in 5 seconds... Error: {e}")
            await asyncio.sleep(5)

async def main():
    # URLs for the two different servers

    args = parse_arguments()
    remoteaddress = args.remoteaddress
    uiadress = args.uiaddress


    server_url1 = args.remoteaddress
    server_url2 = args.uiaddress  # Assuming the second server is on port 8001
    # Create tasks for managing connections to both servers
    task1 = asyncio.create_task(manage_connection(server_url1))
    task2 = asyncio.create_task(manage_connection(server_url2))
    # Wait for both tasks to complete
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())