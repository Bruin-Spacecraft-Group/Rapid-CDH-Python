"""
Task to communicate with CDH over an RS485 bus.
"""

import asyncio
import board
import microcontroller
import busio
import digitalio


async def inter_subsystem_rs485_reciever_task():
    """
    Task that receives any RS485 message and lights up the LED for 1 second if successfully received data.
    """
    led = digitalio.DigitalInOut(board.LED1)
    led.direction = digitalio.Direction.OUTPUT

    uart = busio.UART(
        microcontroller.pin.PB13, microcontroller.pin.PB12, baudrate=50000
    )
    # pins defined for the STM32H743

    te = digitalio.DigitalInOut(microcontroller.pin.PA15)
    te.direction = digitalio.Direction.OUTPUT
    te.value = False

    while True:
        data = uart.read(32)  # read up to 32 bytes
        # print(data)

        if data is not None:
            led.value = True
            print("Data received: ", list(data))
            await asyncio.sleep(1)
            led.value = False
            await asyncio.sleep(1)

        else:
            print("Error receiving data")
