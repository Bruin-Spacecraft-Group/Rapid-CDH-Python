import digitalio
import busio
import time

import asyncio
import pin_manager


class ADS1118_MUX_SELECT:
    CH0_SINGLE_END = 4
    CH1_SINGLE_END = 5
    CH2_SINGLE_END = 6
    CH3_SINGLE_END = 7
    CH0_CH1_DIFF = 0
    CH0_CH3_DIFF = 1
    CH1_CH3_DIFF = 2
    CH2_CH3_DIFF = 3
    TEMPERATURE = 255


class ADS1118_FSR:
    FSR_6144V = 0
    FSR_4096V = 1
    FSR_2048V = 2
    FSR_1024V = 3
    FSR_0512V = 4
    FSR_0256V = 5  # 6 and 7 are also valid here


class ADS1118_SAMPLE_RATE:
    RATE_8 = 0
    RATE_16 = 1
    RATE_32 = 2
    RATE_64 = 3
    RATE_128 = 4
    RATE_250 = 5
    RATE_475 = 6
    RATE_860 = 7


ADS1118_LSB_SIZES = dict(
    [
        (ADS1118_FSR.FSR_6144V, 187.5e-6),
        (ADS1118_FSR.FSR_4096V, 125e-6),
        (ADS1118_FSR.FSR_2048V, 62.5e-6),
        (ADS1118_FSR.FSR_1024V, 31.25e-6),
        (ADS1118_FSR.FSR_0512V, 15.625e-6),
        (ADS1118_FSR.FSR_0256V, 7.8125e-6),
    ]
)
ADS1118_SPS_DELAYS = dict(
    [
        (ADS1118_SAMPLE_RATE.RATE_8, 0.125),
        (ADS1118_SAMPLE_RATE.RATE_16, 0.063),
        (ADS1118_SAMPLE_RATE.RATE_32, 0.032),
        (ADS1118_SAMPLE_RATE.RATE_64, 0.016),
        (ADS1118_SAMPLE_RATE.RATE_128, 0.008),
        (ADS1118_SAMPLE_RATE.RATE_250, 0.004),
        (ADS1118_SAMPLE_RATE.RATE_475, 0.003),
        (ADS1118_SAMPLE_RATE.RATE_860, 0.002),
    ]
)
ADS1118_SPI_RESET_TIME = 0.030  # ideally 28ms, but give it some wiggle room


class ADS1118:
    def __init__(self, sck, mosi, miso, ss):
        pm = pin_manager.PinManager.get_instance()
        self.spi_bus = pm.create_spi(sck, mosi, miso)
        self.drdy_gpio = pm.create_digital_in_out(miso)
        self.ss_gpio = pm.create_digital_in_out(ss)
        with self.ss_gpio as ss:
            ss.direction = digitalio.Direction.OUTPUT
            ss.value = True

    # Returns either the voltage in volts, or the temperature in degrees Celsius
    async def take_sample(
        self,
        channel,
        input_range=ADS1118_FSR.FSR_4096V,
        sample_rate=ADS1118_SAMPLE_RATE.RATE_128,
    ):
        ADS1118._check_sampling_params(channel, input_range, sample_rate)
        transmit_buffer = ADS1118._build_config_register_bytearray(
            channel, input_range, sample_rate
        )
        receive_buffer = bytearray([0, 0])

        data_ready = False

        while not data_ready:

            # send data-getting command
            with self.spi_bus as spi, self.ss_gpio as ss:
                spi.try_lock()
                spi.configure(baudrate=1000000, polarity=0, phase=1)
                ss.direction = digitalio.Direction.OUTPUT
                ss.value = False
                spi.write_readinto(transmit_buffer, receive_buffer)
                ss.value = True
                spi.unlock()

            # wait for data to be ready
            await asyncio.sleep(ADS1118_SPS_DELAYS[sample_rate])

            # check if data is ready
            with self.drdy_gpio as drdy, self.ss_gpio as ss:
                ss.direction = digitalio.Direction.OUTPUT
                ss.value = False
                # busy-wait for CS to DRDY propogation time, unless it takes so long that the
                # ADC resets its SPI peripheral (at which point, quit looking for DRDY and retry
                # the whole transaction)
                # don't do this async because we're currently holding onto hardware
                # we've already waited the delay time above so this should be near-instant
                t0 = time.monotonic_ns()
                while (not data_ready) and (
                    (time.monotonic_ns() - t0) < ADS1118_SPI_RESET_TIME
                ):
                    data_ready = not drdy.value
                ss.value = True

        with self.spi_bus as spi, self.ss_gpio as ss:
            spi.try_lock()
            spi.configure(baudrate=1000000, polarity=0, phase=1)
            ss.direction = digitalio.Direction.OUTPUT
            ss.value = False
            spi.write_readinto(transmit_buffer, receive_buffer)
            ss.value = True
            spi.unlock()

        if channel == ADS1118_MUX_SELECT.TEMPERATURE:
            return ADS1118._temperature_from_bytes(receive_buffer)
        else:
            return ADS1118._voltage_from_bytes(receive_buffer, input_range)

    def _check_sampling_params(channel, input_range, sample_rate):
        assert channel == ADS1118_MUX_SELECT.TEMPERATURE or (
            type(channel) == int and channel >= 0 and channel < 8
        )
        assert type(input_range) == int and input_range >= 0 and input_range < 8
        assert type(sample_rate) == int and sample_rate >= 0 and sample_rate < 8

    def _build_config_register_bytearray(channel, input_range, sample_rate):
        return bytearray(
            [
                (0b1 << 7)
                | ((channel & 0b111) << 4)
                | ((input_range & 0b111) << 1)
                | 1,
                ((sample_rate & 0b111) << 5)
                | ((channel == ADS1118_MUX_SELECT.TEMPERATURE) << 4)
                | 0b1010,
            ]
        )

    def _int_from_two_bytes_signed_be(buffer):
        sum = 0
        if buffer[0] & 0x80:
            sum -= 65536
        sum += 256 * buffer[0]
        sum += buffer[1]
        return sum

    def _temperature_from_bytes(receive_buffer):
        reading = ADS1118._int_from_two_bytes_signed_be(receive_buffer) >> 2
        return reading * 0.03125

    def _voltage_from_bytes(receive_buffer, fsr):
        lsb_size = ADS1118_LSB_SIZES[fsr]
        return ADS1118._int_from_two_bytes_signed_be(receive_buffer) * lsb_size
