import mmap
import os
import struct
import asyncio
import json
import websockets

TARGET_ADDR = 0x40000000
MAP_LENGTH = 4096
WRITE_ADDR = 0x50000000

# Mapping of control instructions to binary values
control_mapping = {
    'back': 0b00,
    'front': 0b01,
    'right': 0b10,
    'left': 0b11,
}

async def receive_and_process_control(websocket, server_url):
    mem_fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    try:
        with mmap.mmap(fileno=mem_fd, length=MAP_LENGTH, offset=WRITE_ADDR, access=mmap.ACCESS_WRITE) as mm:
            async for message in websocket:
                control_data = json.loads(message)
                print(f"Received control instructions from {server_url}: ", control_data)

                command = control_data.get("command")  # Extract the command from the control_data
                if command in control_mapping:
                    # Convert the control instruction to the corresponding binary value
                    value = control_mapping[command]
                    # Write the value to the specified memory address
                    mm.seek(0)  # Move to the beginning of the mmap
                    mm.write(struct.pack('I', value))  # Assuming we're writing an unsigned int (adjust as needed)
                else:
                    print(f"""'{command}' is not a valid instruction. Retry with any of: 
                          - back
                          - front
                          - right
                          - left
                          """)
    finally:
        os.close(mem_fd)

async def send_telemetry(websocket):
    mem_fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    try:
        with mmap.mmap(fileno=mem_fd, length=MAP_LENGTH, offset=TARGET_ADDR, access=mmap.ACCESS_READ) as mm:
            while True:
                mm.seek(0)
                data = mm.read(4*23)  # Adjust based on actual size
                unpacked_data = struct.unpack('23f', data)  # Adjust '23f' based on actual structure

                telemetry_data = {
                    "position": unpacked_data[0],
                    "velocity": unpacked_data[1],
                    "rotation": unpacked_data[2],
                    "acceleration": unpacked_data[3],
                    "cg_angle": unpacked_data[4],
                    "cg_angular_velocity": unpacked_data[5],
                    "battery": unpacked_data[6],
                    "motor_amps": [unpacked_data[7], unpacked_data[8]],
                    "rawdata": {
                        "accel": {"x": unpacked_data[9], "y": unpacked_data[10], "z": unpacked_data[11]},
                        "gyro": {"x": unpacked_data[12], "y": unpacked_data[13], "z": unpacked_data[14]},
                        "enc_left": {"position": unpacked_data[15], "velocity": unpacked_data[16]},  # Example, adjust as needed
                        "enc_right": {"position": unpacked_data[17], "velocity": unpacked_data[18]},  # Example, adjust as needed
                        "adc_battery": {"voltage": unpacked_data[19]},
                        "adc_motor_left": {"voltage": unpacked_data[20]},
                        "adc_motor_right": {"voltage": unpacked_data[21]}
                    }
                }
                print(f"Telemetry Data: {json.dumps(telemetry_data, indent=2)}")

                await websocket.send(json.dumps(telemetry_data))
                await asyncio.sleep(1)

    finally:
        os.close(mem_fd)

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
    server_url1 = 'ws://0.0.0.0:8000'
    server_url2 = 'ws://0.0.0.0:8001'  # Assuming the second server is on port 8001
    # Create tasks for managing connections to both servers
    task1 = asyncio.create_task(manage_connection(server_url1))
    task2 = asyncio.create_task(manage_connection(server_url2))
    # Wait for both tasks to complete
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())


