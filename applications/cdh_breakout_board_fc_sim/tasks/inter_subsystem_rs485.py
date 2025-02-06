"""
Task to communicate with other subsystems over an RS485 bus.
"""

import asyncio
import board
import microcontroller
import busio
import digitalio


async def inter_subsystem_rs485_sender_task():
    """
    Task that sends 0xFFEEDDCC and lights up the LED for 1 second if write is successful.
    """
    led = digitalio.DigitalInOut(board.LED1)
    led.direction = digitalio.Direction.OUTPUT

    uart = busio.UART(
        microcontroller.pin.PB13, microcontroller.pin.PB12, baudrate=50000
    )
    # pins defined for the STM32H743

    te = digitalio.DigitalInOut(microcontroller.pin.PA15)
    te.direction = digitalio.Direction.OUTPUT

    while True:
        te.value = True
        data = bytearray([0] * 4)
        data[0] = (0xFF000000) >> 24
        data[1] = (0xEE0000) >> 16
        data[2] = (0xDD00) >> 8
        data[3] = (0xCC) >> 0

        print("Data to be sent: ", list(data))

        write = uart.write(data)
        te.value = False

        if write:
            led.value = True
            print("Data sent, number of bytes sent: ", write)
            await asyncio.sleep(1)
            led.value = False
            await asyncio.sleep(1)
        else:
            print("Error sending data")
