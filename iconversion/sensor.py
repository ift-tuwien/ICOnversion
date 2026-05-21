"""Support for specifying sensor"""

# -- Imports ------------------------------------------------------------------

from pint import Quantity

from iconversion.utility import ADC_MAX_VALUE

# -- Classes ------------------------------------------------------------------


# pylint: disable=too-few-public-methods


class Sensor:
    """Base class for a general sensor

    Args:

        offset:

            Offset from 0 for the given sensor, e.g. -1/2 for a sensor with
            symmetric value range from -max to max

        coefficients:

           Polynomial coefficients for the sensor; The values are stored in
           the form {0: a₀, 1: a₁, 2: a₂, …}, e.g {1: 200} for a linear sensor
           with the polynom 200·x¹ + 0·x⁰ = 200·x

    """

    def __init__(
        self, offset: float, coefficients: dict[float, float], unit: Quantity
    ) -> None:
        self.offset = offset
        self.coefficients = coefficients
        self.unit = unit

    def convert(self, raw: int) -> float:
        """Convert 16 bit value to physical value

        Args:

            raw:

                A 16 bit raw ADC value

        Returns:

            The physical value

        Examples:

            Import required libraries

            >>> from math import isclose
            >>> from iconversion import g0

            Create a ±100g sensor

            >>> sensor_100g = Sensor(offset=-1 / 2, coefficients={1: 200},
            ...                      unit=g0)

            Convert the value and add unit information

            >>> mean_16_bit = ADC_MAX_VALUE/2
            >>> mean_100g = sensor_100g.convert(mean_16_bit) * sensor_100g.unit
            >>> isclose(mean_100g.magnitude, 0)
            True
            >>> f"{mean_100g:~P}" # Short pretty printed version
            '0.0 g_0'

            Check expected conversion values

            >>> min_16_bit = 0
            >>> min_100g = sensor_100g.convert(min_16_bit)
            >>> isclose(min_100g, -100)
            True

            >>> max_16_bit = ADC_MAX_VALUE
            >>> max_100g = sensor_100g.convert(max_16_bit)
            >>> isclose(max_100g, 100)
            True

        """

        factor = raw / ADC_MAX_VALUE + self.offset

        value = 0
        for order, coefficient in self.coefficients.items():
            value += factor * coefficient**order

        return value


# pylint: enable=too-few-public-methods
