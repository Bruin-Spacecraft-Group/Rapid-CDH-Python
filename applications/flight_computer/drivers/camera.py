import digitalio


class Resolution:
    RES_320x240 = 1
    RES_640x480 = 2
    RES_1280x720 = 4
    RES_1600x1200 = 6
    RES_1920x1080 = 7
    RES_2592x1944 = 9
    RES_96x96 = 10
    RES_128x128 = 11
    RES_320x320 = 12


class Camera:
    def __init__(self, spi, cs):
        """
        Instantiates an camera using the provided SPI bus and chip select pin.
        `spi` should be a `busio.SPI` object.
        `cs` should be a `Pin` object.
        """
        self.spi = spi
        self.cs = digitalio.DigitalInOut(cs)
        self._regw_bufw = bytearray([0] * 2)
        self._regw_bufr = bytearray([0] * 2)
        self._regr_bufw = bytearray([0] * 3)
        self._regr_bufr = bytearray([0] * 3)
        self._last_byte = 0x00

    def _write_register(self, addr, value):
        self._regw_bufw[0] = addr | 0x80
        self._regw_bufw[1] = value
        self.cs.value = False
        self.spi.write_readinto(self._regw_bufw, self._regw_bufr)
        self.cs.value = True

    def _read_register(self, addr):
        self._regr_bufw[0] = addr & 0x7F
        self.cs.value = False
        self.spi.write_readinto(self._regr_bufw, self._regr_bufr)
        self.cs.value = True
        return self._regr_bufr[2]

    def configure(self, resolution):
        """
        Sets up the camera for picture taking. This involves:
        (1) configuring the chip select pin
        (2) sending some SPI commands to the camera.
        This method expects that the lock on `self.spi` is already held and that the
        SPI bus itself is already properly configured, since this bus may be shared.
        """
        self.cs.direction = digitalio.Direction.OUTPUT
        self.cs.value = True
        self._write_register(0x07, (1 << 6))
        self._write_register(0x0A, 0x78)
        self._write_register(0x20, 0x01)
        self._write_register(0x21, resolution)

    def generate_image(self):
        """
        Returns a generator that produces each byte of a captured image
        """

        # start capture and wait for it to finish
        self._write_register(0x04, 0x01)
        self._write_register(0x04, 0x32)
        while (self._read_register(0x41) & 0x08) == 0:
            pass
            # await asyncio.sleep(0)

        # read the buffer over SPI and return it through the generator
        len1 = self._read_register(0x42)
        len2 = self._read_register(0x43)
        len3 = self._read_register(0x44)
        length = (len3 << 16) | (len2 << 8) | len1
        processing_state = 0
        while length > 0:
            this_byte = self._read_register(0x3D)
            # await asyncio.sleep(0)
            if (self._last_byte == 0xFF) and (this_byte == 0xD8):
                yield 0xFF
                processing_state = 1
            if processing_state == 1:
                yield this_byte
            if (self._last_byte == 0xFF) and (this_byte == 0xD9):
                processing_state == 2
            self._last_byte = this_byte
            length -= 1
