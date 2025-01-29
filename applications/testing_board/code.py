import board
import busio

import asyncio

inter_subsystem_spi_bus = busio.SPI(
    clock=board.D12,
    MOSI=board.D13,
    MISO=board.D11,
    SS=board.D10,
    slave_mode=True,
)
while not inter_subsystem_spi_bus.try_lock():
    pass
inter_subsystem_spi_bus.configure()  # baudrate, polarity, etc. available here as kw params


async def send_receive(transmit_buffer, receive_buffer):
    inter_subsystem_spi_bus.async_transfer_start(transmit_buffer, receive_buffer)
    while not inter_subsystem_spi_bus.async_transfer_finished():
        await asyncio.sleep(0)
    inter_subsystem_spi_bus.async_transfer_end()


sensor_value = 0x10203040
spi_read_bytes = bytearray([0] * 4)
spi_write_bytes = bytearray([0] * 4)


async def spi_write_task():
    global spi_read_bytes, spi_write_bytes, sensor_value, inter_subsystem_spi_bus
    while True:
        # communicates data back to CDH
        spi_write_bytes[0] = (sensor_value & 0xFF000000) >> 24
        spi_write_bytes[1] = (sensor_value & 0xFF0000) >> 16
        spi_write_bytes[2] = (sensor_value & 0xFF00) >> 8
        spi_write_bytes[3] = (sensor_value & 0xFF) >> 0
        await send_receive(spi_write_bytes, spi_read_bytes)


async def sensor_read_task():
    # regularly updates `sensor_value` based on the feedback from the sensor
    global sensor_value
    while True:
        sensor_value += 1
        await asyncio.sleep(0.2)


async def feedback_task():
    # send debug data to the USB serial regularly
    global sensor_value, spi_read_bytes, spi_write_bytes
    while True:
        print("TST wrote", list(bytes(spi_write_bytes)), "to SPI")  # fix with [:-1]
        print("TST read", list(bytes(spi_read_bytes)), "from SPI")  # fix with [:-1]
        await asyncio.sleep(1)


async def gathered_task():
    await asyncio.gather(spi_write_task(), sensor_read_task(), feedback_task())


if __name__ == "__main__":
    asyncio.run(gathered_task())
