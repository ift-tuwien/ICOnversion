"""Support for specifying sensor"""

# -- Imports ------------------------------------------------------------------

from pathlib import Path
from typing import NamedTuple

from numpy.polynomial import Polynomial
from pint import Quantity
from ruamel.yaml import YAML

from iconversion import ureg
from iconversion.utility import ADC_MAX_VALUE

# -- Functions ----------------------------------------------------------------


def read_sensor_data():
    """Read sensor data from config file

    Examples:

        Read sensor data

        >>> sensors = read_sensor_data()
        >>> sensors["acc100g_01"]
        -100.0 g – 100.0 g (0.0 + 200.0·x)

    """

    yaml = YAML(typ="safe")
    sensors = {}
    for sensor in yaml.load(Path(__file__).parent / "sensors.yaml")["sensors"]:
        sensor_id = sensor["id"]
        offset = sensor["offset"]
        coefficients = sensor["coefficients"]
        sensor_range = SensorRange(
            min=sensor["phys_min"], max=sensor["phys_max"]
        )
        unit = ureg.parse_units(sensor["unit"])
        sensors[sensor_id] = Sensor(offset, coefficients, sensor_range, unit)

    return sensors


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
           the form [a₀, a₁, a₂, …], e.g [0, 200] for a linear sensor
           with the polynom 0·x⁰ + 200·x¹ = 200·x

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
        ...                      coefficients=[0, 200],
        ...                      sensor_range=SensorRange(min=-100, max=100),
        ...                      unit=g0)

    """

    def __init__(
        self,
        offset: float,
        coefficients: list[float],
        sensor_range: SensorRange,
        unit: Quantity,
    ) -> None:
        self.offset = offset
        self.polynomial = Polynomial(coefficients)
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
            ...     coefficients=[0, 200],
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

        return self.polynomial(factor)

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
            ...     coefficients=[2, 10, 4, 0, 0, 6],
            ...     sensor_range=SensorRange(min=0, max=100),
            ...     unit=degree_Celsius)
            0 °C – 100 °C (2.0 + 10.0·x + 4.0·x² + 0.0·x³ + 0.0·x⁴ + 6.0·x⁵)

            Print representation of a ±100g acceleration sensor

            >>> Sensor(offset=-1 / 2,
            ...     coefficients=[0, 200],
            ...     sensor_range=SensorRange(min=-100, max=100),
            ...     unit=g0)
            -100 g_0 – 100 g_0 (0.0 + 200.0·x)

        """

        polynomial = self.polynomial
        sensor_range = self.range
        unit = self.unit
        representation = (
            f"{sensor_range.min} {unit:~P} – {sensor_range.max} {unit:~P} "
            f"({polynomial:unicode})"
        )

        return representation
