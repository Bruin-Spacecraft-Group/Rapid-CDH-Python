import digitalio
import busio


class ManagedPin:
    def __init__(self, pin):
        self.pin = pin
        self.claimer = DefaultPinClaimer(self)


class ManagedDevice:
    def __init__(self, managed_pins, device_producer):
        self._managed_pins = managed_pins
        self._device_producer = device_producer
        self._instance = None
        self._active_contexts = 0

    # True if a call to __enter__() would do nothing to the hardware because
    # a context for this device is already active (or an explicit call to
    # __enter__() has been made)
    def is_running(self):
        return self._instance is not None

    # True if a call to _reclaim() would result in an exception, since
    # a context for this device is still active. Calling __exit__() destroys
    # an active context for the device
    # if a device is not running, it cannot be busy
    def is_busy(self):
        return self._active_contexts != 0

    def _reclaim(self):
        if self._active_contexts != 0:
            raise RuntimeError("Cannot reclaim device which is still open")
        self._instance.deinit()
        self._instance = None
        for m_pin in self._managed_pins:
            m_pin.claimer = DefaultPinClaimer(m_pin)

    # Set the pins this device requires to be active and configured for this device
    # until the next call to _reclaim(). Also increments the number of contexts in
    # which this device is considered to be open and unable to be reclaimed
    def __enter__(self):
        if self._instance is not None:
            self._active_contexts += 1
            return self._instance
        for m_pin in self._managed_pins:
            if m_pin.claimer.is_running():
                m_pin.claimer._reclaim()
        for m_pin in self._managed_pins:
            m_pin.claimer._reclaim()
        self._instance = self._device_producer()
        for m_pin in self._managed_pins:
            m_pin.claimer = self
            m_pin.is_claimed = True
        self._active_contexts += 1
        return self._instance

    # Decrements the number of contexts in which this device is considered to be open
    def __exit__(self, exc_type, exc, exc_trace):
        self._active_contexts -= 1


class DefaultPinClaimer:
    def __init__(self, managed_pin):
        self.m_pin = managed_pin
        self._instance = digitalio.DigitalInOut(self.m_pin.pin)

    def is_running(self):
        return self._instance is not None

    def is_busy(self):
        return False

    def _reclaim(self):
        if self._instance is not None:
            self._instance.deinit()
            self._instance = None


class PinManager:
    _instance = None

    def get_instance():
        if PinManager._instance is None:
            PinManager._instance = PinManager()
        return PinManager._instance

    def __init__(self):
        self._pins = dict()
        self._devices = dict()

    def _get_pin_reference(self, pin):
        if pin not in self._pins:
            self._pins[pin] = ManagedPin(pin)
        return self._pins[pin]

    def _create_general_device(self, pins, device_type, device_producer):
        m_pins = [self._get_pin_reference(pin) for pin in pins]
        device_key = tuple(m_pins + [device_type])
        if device_key not in self._devices:
            self._devices[device_key] = ManagedDevice(m_pins, device_producer)
        return self._devices[device_key]

    def create_digital_in_out(self, pin):
        return self._create_general_device(
            [pin],
            digitalio.DigitalInOut,
            (lambda: digitalio.DigitalInOut(pin)),
        )

    def create_spi(self, clock, MOSI, MISO):
        return self._create_general_device(
            [clock, MOSI, MISO],
            busio.SPI,
            (lambda: busio.SPI(clock, MOSI, MISO)),
        )

    def create_i2c(self, scl, sda, frequency=100000):
        return self._create_general_device(
            [scl, sda],
            busio.I2C,
            (lambda: busio.I2C(scl, sda, frequency=frequency)),
        )
