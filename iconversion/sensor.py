"""Support for specifying sensor"""

# -- Imports ------------------------------------------------------------------

from typing import NamedTuple

from pint import Quantity

from iconversion.utility import ADC_MAX_VALUE

# -- Classes ------------------------------------------------------------------


class SensorRange(NamedTuple):
    """Physical range of sensor values"""

    min: float
    """Minimum physical value of a sensor"""

    max: float
    """Maximum physical value of a sensor"""


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

        sensor_range:

            The minimum and maximum physical values of the sensor

        unit:

            The physical unit of the sensor output

    Examples:

        Import required libraries

        >>> from math import isclose
        >>> from iconversion import g0

        Create a ±100g sensor

        >>> sensor_100g = Sensor(offset=-1 / 2,
        ...                      coefficients={1: 200},
        ...                      sensor_range=SensorRange(min=-100, max=100),
        ...                      unit=g0)

    """

    def __init__(
        self,
        offset: float,
        coefficients: dict[float, float],
        sensor_range: SensorRange,
        unit: Quantity,
    ) -> None:
        self.offset = offset
        self.coefficients = sorted(coefficients.items())
        self.range = sensor_range
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

            >>> sensor_100g = Sensor(offset=-1 / 2,
            ...     coefficients={1: 200},
            ...     sensor_range=SensorRange(min=-100, max=100),
            ...     unit=g0)

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
        for order, coefficient in self.coefficients:
            value += coefficient * factor**order

        return value

    def __repr__(self):
        """Get the string representation of the sensor

        Returns:

            A text representing this sensor

        Examples:

            Import required libraries

            >>> from iconversion import degree_Celsius, g0

            Print representation of a temperature sensor

            >>> Sensor(
            ...     offset=0,
            ...     coefficients={0: 2, 1: 10, 2: 4, 5: 6},
            ...     sensor_range=SensorRange(min=0, max=100),
            ...     unit=degree_Celsius)
            0 °C – 100 °C (2 + 10·x + 4·x² + 6·x⁵)

            Print representation of a ±100g acceleration sensor

            >>> Sensor(offset=-1 / 2,
            ...     coefficients={1: 200},
            ...     sensor_range=SensorRange(min=-100, max=100),
            ...     unit=g0)
            -100 g_0 – 100 g_0 (200·x)

        """

        def number_to_power(number: int) -> str:
            digit_to_power = dict(enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹"))
            representation = ""
            remainder = number
            if remainder == 0:
                return digit_to_power[0]
            while remainder > 0:
                last_digit = remainder % 10
                remainder = remainder // 10
                representation = digit_to_power[last_digit] + representation

            return representation

        def repr_x(order: int) -> str:
            if order <= 0:
                return ""
            if order <= 1:
                return "·x"
            return f"·x{number_to_power(order)}"

        coefficient_representation = " + ".join(
            f"{coefficient}{repr_x(order)}"
            for order, coefficient in self.coefficients
        )

        sensor_range = self.range
        unit = self.unit
        representation = (
            f"{sensor_range.min} {unit:~P} – {sensor_range.max} {unit:~P} "
            f"({coefficient_representation})"
        )

        return representation
