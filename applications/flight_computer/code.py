import asyncio
import microcontroller
import analogio
from drivers.ads1118 import (
    ADS1118,
    ADS1118_MUX_SELECT,
    ADS1118_FSR,
    ADS1118_SAMPLE_RATE,
)


def test_ads1118():
    adc = ADS1118(
        microcontroller.pin.PA13,
        microcontroller.pin.PA12,
        microcontroller.pin.PA14,
        microcontroller.pin.PB17,
    )
    print("temp:", asyncio.run(adc.take_sample(ADS1118_MUX_SELECT.TEMPERATURE)))

    aout = analogio.AnalogOut(microcontroller.pin.PA05)

    def vtoi(x):
        return int(x / 3.1 * 65535)

    for i in range(101):
        x = 0.031 * i
        aout.value = vtoi(x)
        y = asyncio.run(adc.take_sample(ADS1118_MUX_SELECT.CH1_SINGLE_END))
        print(x, ",", y)


if __name__ == "__main__":
    test_ads1118()
