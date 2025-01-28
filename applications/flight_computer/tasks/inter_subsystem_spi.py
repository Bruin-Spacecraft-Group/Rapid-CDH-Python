import board
import busio
import digitalio

import asyncio
import pin_manager


pm = pin_manager.PinManager.get_instance()

inter_subsystem_spi_bus = pm.create_spi(clock=board.D12, MOSI=board.D13, MISO=board.D10)
inter_subsystem_spi_bus = inter_subsystem_spi_bus.__enter__()
while not inter_subsystem_spi_bus.try_lock():
    pass
inter_subsystem_spi_bus.configure()  # baudrate, polarity, etc. available here as kw params

test_board_cs = pm.create_digital_in_out(board.D2)
test_board_cs = test_board_cs.__enter__()

message_count = 0
spi_read_bytes = bytearray([0] * 4)
spi_write_bytes = bytearray([0] * 4)


async def inter_subsystem_spi_task():
    global spi_write_bytes, spi_read_bytes, test_board, message_count
    while True:
        # communicates commands with subsystem X
        spi_write_bytes[0] = (message_count & 0xFF000000) >> 24
        spi_write_bytes[1] = (message_count & 0xFF0000) >> 16
        spi_write_bytes[2] = (message_count & 0xFF00) >> 8
        spi_write_bytes[3] = (message_count & 0xFF) >> 0
        test_board_cs.value = False
        inter_subsystem_spi_bus.write_readinto(spi_write_bytes, spi_read_bytes)
        test_board_cs.value = True
        message_count += 1
        await asyncio.sleep(0.01)


async def inter_subsystem_spi_debug_task():
    # send debug data to the USB serial regularly
    global spi_write_bytes, spi_read_bytes
    while True:
        print("CDH wrote", list(bytes(spi_write_bytes)), "to SPI")
        print("CDH read", list(bytes(spi_read_bytes)), "from SPI")
        await asyncio.sleep(1)
