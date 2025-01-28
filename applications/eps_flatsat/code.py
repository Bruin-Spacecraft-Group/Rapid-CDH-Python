import microcontroller
import digitalio
import busio

import asyncio
import time


async def battey_management_task():
    while True:
        await asyncio.sleep(0)


async def output_bus_control_task():
    while True:
        await asyncio.sleep(0)


async def data_recording_task():
    while True:
        await asyncio.sleep(0)


async def intersubsystem_communication_task():
    while True:
        await asyncio.sleep(0)


async def gathered_task():
    await asyncio.gather(
        battey_management_task(),
        output_bus_control_task(),
        data_recording_task(),
        intersubsystem_communication_task(),
    )


if __name__ == "__main__":
    asyncio.run(gathered_task())
