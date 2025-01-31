"""
Manager class to allow a single pin to be used by multiple devices and allow device
drivers to work directly with pins.

A PinManager creates and returns a ManagedDevice from a set of pins when requested. A
variety of types of ManagedDevice are supported, from analog inputs to SPI buses. Once
a pin has been provided to the PinManager, it will appear in use to any other software
that attempts to create a device using the pin. However, the PinManager itself may
create additional devices that refer to the same pin. Deinitialization is handled when
user code interacts with each ManagedDevice it has created.

To use a ManagedDevice as though it has the same type as the CircuitPython peripheral
driver class that it boxes, user code must open a context managing the device. For
example:
```py
pm = PinManager.get_instance()
m_dio = pm.create_digital_in_out(microcontroller.pin.PA00)
with m_dio as gpio:
    gpio.direction = digitalio.Direction.OUTPUT
    gpio.value = True
print("Turned on gpio!")
```
When the context managing the device is closed, the pins used by the device are free to
be used by other peripherals, but each of these peripherals must also be controlled by a
ManagedDevice from the same PinManager.

For efficiency reasons, each ManagedDevice is cached so that if an identical ManagedDevice
is created elsewhere, no unnecessary initialization and deinitialization occurs. Further,
ManagedDevice deinitialization is handled lazily, firstly allowing pins to hold their
state until explicitly changed by some other task and secondly allowing the ManagedDevice
caching to provide an efficiency benefit to the overall system.

If a context is created which uses a pin, but that contexts cannot be created due to
contention with an existing context on a distinct ManagedDevice, a RuntimeError will be
raised. User code should close any contexts used in multiple tasks before yielding to
guarantee this condition does not arise.
"""

import digitalio
import busio
import analogio


class _ManagedPin:
    def __init__(self, pin):
        self.pin = pin
        self.claimer = _DefaultPinClaimer(self)


class ManagedDevice:
    """
    A boxed hardware peripheral controller device provided by a PinManager to be managed
    and used within a context opened in user code.
    """

    def __init__(self, managed_pins, device_producer):
        self._managed_pins = managed_pins
        self._device_producer = device_producer
        self._instance = None
        self._active_contexts = 0

    # True if a call to __enter__() would do nothing to the hardware because
    # a context for this device is already active (or an explicit call to
    # __enter__() has been made)
    def is_running(self):
        """
        Returns whether this device is running.

        Specifically, this method returns True if a call to __enter__() would do no hardware
        reconfiguration. If a context for this device is already active, this condition holds.
        Alternatively, since device deinitialization happens lazily, this condition can hold
        when a context for this device was formerly opened and is no longer active but no
        contending device has yet caused deinitialization.
        """
        return self._instance is not None

    # True if a call to _reclaim() would result in an exception, since
    # a context for this device is still active. Calling __exit__() destroys
    # an active context for the device
    # if a device is not running, it cannot be busy
    def is_busy(self):
        """
        Returns whether this device has any active contexts.

        Specifically, this method returns True if a call to _reclaim() result in an exception.
        _reclaim() should not be called explicitly, but if a context is opened for a device
        that contents for hardware with this device, it will be called implicitly.

        Any device which is busy must be running. Note that a device which appears to have no
        open contexts may have open contexts as a result of aliasing, since identical devices
        are cached and merged upon creation to maximize efficiency.
        """
        return self._active_contexts != 0

    def _reclaim(self):
        if self._active_contexts != 0:
            raise RuntimeError("Cannot reclaim device which is still open")
        self._instance.deinit()
        self._instance = None
        for m_pin in self._managed_pins:
            m_pin.claimer = _DefaultPinClaimer(m_pin)

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


class _DefaultPinClaimer:
    def __init__(self, managed_pin):
        self.m_pin = managed_pin
        self._instance = digitalio.DigitalInOut(self.m_pin.pin)

    def is_running(self):
        """
        Implementation of ManagedDevice.is_running() for a _DefaultPinClaimer
        """
        return self._instance is not None

    def is_busy(self):
        """
        Implementation of ManagedDevice.is_busy() for a _DefaultPinClaimer
        """
        return False

    def _reclaim(self):
        if self._instance is not None:
            self._instance.deinit()
            self._instance = None


class PinManager:
    """
    Object that manages pins for an embedded CircuitPython application. See module
    documentation for details.
    """

    _instance = None

    @staticmethod
    def get_instance():
        """
        Creates a PinManager and caches one if none exists, or returns the existing PinManager
        if one has already been created. This method allows this class to be used according to
        the singleton pattern.
        """
        if PinManager._instance is None:
            PinManager._instance = PinManager()
        return PinManager._instance

    def __init__(self):
        self._pins = {}
        self._devices = {}

    def _get_pin_reference(self, pin):
        if pin not in self._pins:
            self._pins[pin] = _ManagedPin(pin)
        return self._pins[pin]

    def _create_general_device(self, pins, device_type, device_producer):
        m_pins = [self._get_pin_reference(pin) for pin in pins]
        device_key = tuple(m_pins + [device_type])
        if device_key not in self._devices:
            self._devices[device_key] = ManagedDevice(m_pins, device_producer)
        return self._devices[device_key]

    def create_digital_in_out(self, pin):
        """
        Creates and returns ManagedDevice wrapping a digitalio.DigitalInOut on the specified
        pin, or returns one from the cache if one has already been created.
        """
        return self._create_general_device(
            [pin],
            digitalio.DigitalInOut,
            (lambda: digitalio.DigitalInOut(pin)),
        )

    def create_spi(self, clock, mosi, miso):
        """
        Creates and returns ManagedDevice wrapping a busio.SPI on the three specified pins,
        or returns one from the cache if one has already been created.
        """
        return self._create_general_device(
            [clock, mosi, miso],
            busio.SPI,
            (lambda: busio.SPI(clock, mosi, miso)),
        )

    def create_i2c(self, scl, sda, frequency=100000):
        """
        Creates and returns ManagedDevice wrapping a busio.SPI on the two specified pins
        with the specified clock frequency, or returns one from the cache if one has already
        been created.
        """
        return self._create_general_device(
            [scl, sda],
            (busio.I2C, frequency),
            (lambda: busio.I2C(scl, sda, frequency=frequency)),
        )

    def create_analog_in(self, pin):
        """
        Creates and returns ManagedDevice wrapping a analogio.AnalogIn on the specified
        pin, or returns one from the cache if one has already been created.
        """
        return self._create_general_device(
            [pin],
            analogio.AnalogIn,
            (lambda: analogio.AnalogIn(pin)),
        )
