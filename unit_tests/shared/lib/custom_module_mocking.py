import sys


class HardwareIO_Test:
    def __init__(self):
        self._is_alive = True

    def deinit(self):
        self._is_alive = False

    def __exit__(self):
        self.deinit()

    def __enter__(self, exc_type, exc, exc_trace):
        pass


class DigitalInOut_Test(HardwareIO_Test):
    def __init__(self, gpio):
        super().__init__()
        self._direction = None
        self._value = None

    @property
    def value(self):
        if not self._is_alive:
            raise RuntimeError("Device already deinit")
        return self._value

    @value.setter
    def value(self, pin_state):
        if not self._is_alive:
            raise RuntimeError("Device already deinit")
        self._value = pin_state

    @property
    def direction(self):
        if not self._is_alive:
            raise RuntimeError("Device already deinit")
        return self._direction

    @direction.setter
    def direction(self, pin_state):
        if not self._is_alive:
            raise RuntimeError("Device already deinit")
        self._direction = pin_state


class SPI_Test(HardwareIO_Test):
    def __init__(self, clock, mosi, miso):
        super().__init__()
        self._locked = False

    def try_lock(self):
        if not (self._is_alive):
            raise RuntimeError("device not available")
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self):
        if not (self._is_alive):
            raise RuntimeError("device not available")
        self._locked = False

    def configure(self, *, baudrate=100000, polarity=0, phase=0, bits=8):
        if not (self._is_alive and self._locked):
            raise RuntimeError("device not available")

    def write_readinto(
        self,
        out_buffer,
        in_buffer,
        *,
        out_start=0,
        out_end=sys.maxsize,
        in_start=0,
        in_end=sys.maxsize
    ):
        if not (self._is_alive and self._locked):
            raise RuntimeError("device not available")

    @property
    def frequency(self):
        if not (self._is_alive):
            raise RuntimeError("device not available")
        return 0
