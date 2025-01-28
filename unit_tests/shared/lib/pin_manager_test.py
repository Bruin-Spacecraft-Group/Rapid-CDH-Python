import unittest

import pin_manager
import custom_module_mocking


def create_pin_manager_specific_mocking():
    # replace magicmock with an actual implementation for specific constructors
    # that we're using to test object retention requirements
    pin_manager.digitalio.DigitalInOut = custom_module_mocking.DigitalInOut_Test
    pin_manager.busio.SPI = custom_module_mocking.SPI_Test


class PinManager_Test(unittest.TestCase):

    def test_digital_in_out(self):
        create_pin_manager_specific_mocking()
        inst = pin_manager.PinManager()
        D1_gpio = inst.create_digital_in_out("D1")
        with D1_gpio as pin:
            pin.value = True
            self.assertTrue(pin.value)

    def test_spi(self):
        create_pin_manager_specific_mocking()
        inst = pin_manager.PinManager()
        SPI_bus = inst.create_spi("D1", "D2", "D3")
        with SPI_bus as bus:
            self.assertIsNone(bus.unlock())
            self.assertRaises(RuntimeError, bus.configure)
            self.assertTrue(bus.try_lock())
            self.assertIsNone(bus.configure())
            buf0 = bytearray([0] * 4)
            buf1 = bytearray([0] * 4)
            self.assertIsNone(bus.write_readinto(buf0, buf1))
            self.assertIsNone(bus.unlock())
            self.assertRaises(RuntimeError, bus.configure)
            self.assertIsNone(bus.deinit())
            self.assertRaises(RuntimeError, bus.try_lock)

    def test_context_retention(self):
        create_pin_manager_specific_mocking()
        inst = pin_manager.PinManager()
        spi1 = inst.create_spi("D1", "D2", "D3")
        spi2 = inst.create_spi("D3", "D4", "D5")
        D1_gpio = inst.create_digital_in_out("D1")
        D3_gpio = inst.create_digital_in_out("D3")
        D5_gpio = inst.create_digital_in_out("D5")
        with spi1 as bus:
            self.assertTrue(bus.try_lock())
            self.assertRaises(RuntimeError, D1_gpio.__enter__)
            self.assertRaises(RuntimeError, D3_gpio.__enter__)
            with D5_gpio as pin:
                pass
            self.assertRaises(RuntimeError, spi2.__enter__)
        with spi2 as bus:
            with spi2 as bus:
                self.assertTrue(bus.try_lock())
            with D1_gpio as pin:
                pass
            self.assertRaises(RuntimeError, D3_gpio.__enter__)
            self.assertRaises(RuntimeError, D5_gpio.__enter__)
            self.assertRaises(RuntimeError, spi1.__enter__)

    def test_pin_configuration_swapping(self):
        create_pin_manager_specific_mocking()
        inst = pin_manager.PinManager()
        spi1 = inst.create_spi("D1", "D2", "D3")
        D1_gpio = inst.create_digital_in_out("D1")
        with spi1 as bus:
            self.assertIn("try_lock", dir(bus))
        with D1_gpio as pin:
            self.assertIn("value", dir(pin))
            self.assertRaises(RuntimeError, bus.try_lock)
        with spi1 as bus:
            self.assertIn("try_lock", dir(bus))

            def set_pin_high():
                pin.value = True

            self.assertRaises(RuntimeError, set_pin_high)

    def test_state_functions(self):
        create_pin_manager_specific_mocking()
        inst = pin_manager.PinManager()
        spi = inst.create_spi("D1", "D2", "D3")
        gpio1 = inst.create_digital_in_out("D1")
        print(spi._instance)
        print(gpio1._instance)
        self.assertFalse(spi.is_busy())
        self.assertFalse(gpio1.is_busy())
        with gpio1:
            self.assertFalse(spi.is_busy())
            self.assertTrue(gpio1.is_busy())
            self.assertFalse(spi.is_running())
            self.assertTrue(gpio1.is_running())
            with gpio1:
                self.assertFalse(spi.is_busy())
                self.assertTrue(gpio1.is_busy())
                self.assertFalse(spi.is_running())
                self.assertTrue(gpio1.is_running())
            self.assertFalse(spi.is_busy())
            self.assertTrue(gpio1.is_busy())
            self.assertFalse(spi.is_running())
            self.assertTrue(gpio1.is_running())
        with spi:
            self.assertTrue(spi.is_busy())
            self.assertFalse(gpio1.is_busy())
            self.assertTrue(spi.is_running())
            self.assertFalse(gpio1.is_running())
        self.assertFalse(spi.is_busy())
        self.assertFalse(gpio1.is_busy())


if __name__ == "__main__":
    unittest.main()
