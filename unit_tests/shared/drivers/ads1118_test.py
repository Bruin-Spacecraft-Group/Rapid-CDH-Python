import unittest

import ads1118


class ADS1118_Test(unittest.TestCase):

    _NON_BYTE_OBJECTS = [object(), {}, [], 3.0, -1, 256]

    def test_channel_parameter_validation(self):
        for ch in [
            ads1118.MuxSelection.CH0_SINGLE_END,
            ads1118.MuxSelection.CH1_SINGLE_END,
            ads1118.MuxSelection.CH2_SINGLE_END,
            ads1118.MuxSelection.CH3_SINGLE_END,
            ads1118.MuxSelection.CH0_CH1_DIFF,
            ads1118.MuxSelection.CH0_CH3_DIFF,
            ads1118.MuxSelection.CH1_CH3_DIFF,
            ads1118.MuxSelection.CH2_CH3_DIFF,
            ads1118.MuxSelection.TEMPERATURE,
        ]:
            failure = None
            try:
                ads1118.Ads1118._check_channel_param(ch)
            except AssertionError as e:
                failure = e
            self.assertIsNone(failure)
        for non_byte in ADS1118_Test._NON_BYTE_OBJECTS:
            self.assertRaises(
                AssertionError,
                ads1118.Ads1118._check_channel_param,
                non_byte,
            )
        self.assertRaises(
            AssertionError,
            ads1118.Ads1118._check_channel_param,
            120,
        )

    def test_fsr_validation(self):
        for fsr in [
            ads1118.InputRange.FSR_6_144V,
            ads1118.InputRange.FSR_4_096V,
            ads1118.InputRange.FSR_2_048V,
            ads1118.InputRange.FSR_1_024V,
            ads1118.InputRange.FSR_0_512V,
            ads1118.InputRange.FSR_0_256V,
        ]:
            failure = None
            try:
                ads1118.Ads1118._check_fsr_param(fsr)
            except AssertionError as e:
                failure = e
            self.assertIsNone(failure)
        for non_byte in ADS1118_Test._NON_BYTE_OBJECTS:
            self.assertRaises(
                AssertionError,
                ads1118.Ads1118._check_fsr_param,
                non_byte,
            )
        self.assertRaises(
            AssertionError,
            ads1118.Ads1118._check_fsr_param,
            120,
        )
        self.assertRaises(
            AssertionError,
            ads1118.Ads1118._check_fsr_param,
            255,
        )

    def test_sps_validation(self):
        for sps in [
            ads1118.SamplingRate.RATE_8,
            ads1118.SamplingRate.RATE_16,
            ads1118.SamplingRate.RATE_32,
            ads1118.SamplingRate.RATE_64,
            ads1118.SamplingRate.RATE_128,
            ads1118.SamplingRate.RATE_250,
            ads1118.SamplingRate.RATE_475,
            ads1118.SamplingRate.RATE_860,
        ]:
            failure = None
            try:
                ads1118.Ads1118._check_sps_param(sps)
            except AssertionError as e:
                failure = e
            self.assertIsNone(failure)
        for non_byte in ADS1118_Test._NON_BYTE_OBJECTS:
            self.assertRaises(
                AssertionError,
                ads1118.Ads1118._check_sps_param,
                non_byte,
            )
        self.assertRaises(
            AssertionError,
            ads1118.Ads1118._check_sps_param,
            120,
        )
        self.assertRaises(
            AssertionError,
            ads1118.Ads1118._check_sps_param,
            255,
        )

    def test_parameter_validation(self):

        good_params = [
            (
                ads1118.MuxSelection.CH0_CH1_DIFF,
                ads1118.InputRange.FSR_6_144V,
                ads1118.SamplingRate.RATE_8,
            ),
            (
                ads1118.MuxSelection.CH3_SINGLE_END,
                ads1118.InputRange.FSR_0_256V,
                ads1118.SamplingRate.RATE_860,
            ),
            (
                ads1118.MuxSelection.CH0_SINGLE_END,
                ads1118.InputRange.FSR_4_096V,
                ads1118.SamplingRate.RATE_128,
            ),
            (
                ads1118.MuxSelection.TEMPERATURE,
                ads1118.InputRange.FSR_2_048V,
                ads1118.SamplingRate.RATE_475,
            ),
        ]
        for params in good_params:
            failure = None
            try:
                ads1118.Ads1118._check_sampling_params(params[0], params[1], params[2])
            except AssertionError as e:
                failure = e
            self.assertIsNone(failure)

        # Test with bad parameters
        bad_params = [
            (-1, 0, 0),
            (8, 0, 0),
            (254, 0, 0),
            (256, 0, 0),
            (4.5, 0, 0),
            (0, -1, 0),
            (0, 8, 0),
            (0, 4.5, 0),
            (0, 0, -1),
            (0, 0, 8),
            (0, 0, 4.5),
        ]
        for params in bad_params:
            self.assertRaises(
                AssertionError,
                ads1118.Ads1118._check_sampling_params,
                params[0],
                params[1],
                params[2],
            )

    def test_config_register_format(self):
        self.assertEqual(
            ads1118.Ads1118._build_config_register_bytearray(
                ads1118.MuxSelection.CH0_SINGLE_END,
                ads1118.InputRange.FSR_4_096V,
                ads1118.SamplingRate.RATE_128,
            ),
            b"\xC3\x8A",
        )
        self.assertEqual(
            ads1118.Ads1118._build_config_register_bytearray(
                ads1118.MuxSelection.CH2_CH3_DIFF,
                ads1118.InputRange.FSR_2_048V,
                ads1118.SamplingRate.RATE_860,
            ),
            b"\xB5\xEA",
        )
        self.assertEqual(
            ads1118.Ads1118._build_config_register_bytearray(
                ads1118.MuxSelection.CH0_CH1_DIFF,
                ads1118.InputRange.FSR_6_144V,
                ads1118.SamplingRate.RATE_8,
            ),
            b"\x81\x0A",
        )
        self.assertEqual(
            ads1118.Ads1118._build_config_register_bytearray(
                ads1118.MuxSelection.TEMPERATURE,
                ads1118.InputRange.FSR_0_256V,
                ads1118.SamplingRate.RATE_64,
            ),
            b"\xFB\x7A",
        )

    def test_temperature_conversion(self):
        temp_sensor_data = [
            (0b_01_0000_00, 0b_00_0000_00, 128),
            (0b_00_1111_11, 0b_11_1111_00, 127.96875),
            (0b_00_1100_10, 0b_00_0000_00, 100),
            (0b_00_1001_01, 0b_10_0000_00, 75),
            (0b_00_0110_01, 0b_00_0000_00, 50),
            (0b_00_0011_00, 0b_10_0000_00, 25),
            (0b_00_0000_00, 0b_00_1000_00, 0.25),
            (0b_00_0000_00, 0b_00_0001_00, 0.03125),
            (0b_00_0000_00, 0b_00_0000_00, 0),
            (0b_00_0000_00, 0b_00_0000_10, 0),
            (0b_00_0000_00, 0b_00_0000_01, 0),
            (0b_11_1111_11, 0b_11_1000_00, -0.25),
            (0b_11_1100_11, 0b_10_0000_00, -25),
            (0b_11_1011_00, 0b_00_0000_00, -40),
        ]
        for case in temp_sensor_data:
            self.assertAlmostEqual(
                ads1118.Ads1118._temperature_from_bytes(bytes([case[0], case[1]])),
                case[2],
            )

    def test_voltage_conversion(self):
        for fsr in [
            (ads1118.InputRange.FSR_6_144V, 6.144),
            (ads1118.InputRange.FSR_4_096V, 4.096),
            (ads1118.InputRange.FSR_2_048V, 2.048),
            (ads1118.InputRange.FSR_1_024V, 1.024),
            (ads1118.InputRange.FSR_0_512V, 0.512),
            (ads1118.InputRange.FSR_0_256V, 0.256),
        ]:
            self.assertAlmostEqual(
                ads1118.Ads1118._voltage_from_bytes(b"\x7F\xFF", fsr[0]),
                fsr[1] * (2**15 - 1) / (2**15),
            )
            self.assertAlmostEqual(
                ads1118.Ads1118._voltage_from_bytes(b"\x00\x01", fsr[0]),
                fsr[1] / (2**15),
            )
            self.assertAlmostEqual(
                ads1118.Ads1118._voltage_from_bytes(b"\x00\x00", fsr[0]),
                0,
            )
            self.assertAlmostEqual(
                ads1118.Ads1118._voltage_from_bytes(b"\xFF\xFF", fsr[0]),
                -fsr[1] / (2**15),
            )
            self.assertAlmostEqual(
                ads1118.Ads1118._voltage_from_bytes(b"\x80\x00", fsr[0]),
                -fsr[1],
            )


if __name__ == "__main__":
    unittest.main()
