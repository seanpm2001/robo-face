import asyncio
import json
import websockets
async def receive_and_process_control(websocket):
    while True:
        control_message = await websocket.recv()
        control_data = json.loads(control_message)
        # Process control instructions received from the server
        # Adjust the behavior of the self-balancing robot accordingly
        print("Received control instructions:", control_data)
        # Example: Adjust motor speeds or positions based on control_data

async def send_telemetry(websocket):
    while True:
        # Replace this part with code to gather telemetry data from the self-balancing robot
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
}, "gyro": {
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
                },
                "adc_motor_right": {
                     "voltage": 1.2
                }
            }
        }
        telemetry_message = json.dumps(telemetry_data)
        await websocket.send(telemetry_message)
        await asyncio.sleep(1)  # Adjust refresh time as needed
async def main():
    async with websockets.connect('ws://0.0.0.0:8000') as websocket:
        telemetry_task = asyncio.create_task(send_telemetry(websocket))
        control_task = asyncio.create_task(receive_and_process_control
(websocket))
        # Wait for both tasks to complete
        await asyncio.gather(telemetry_task, control_task)
asyncio.run(main())

