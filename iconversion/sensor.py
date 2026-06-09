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
        Acceleration 100g [-100 g_0, 100 g_0] (-125.0 + 250.0·x)

    """

    yaml = YAML(typ="safe")
    sensors = {}
    for sensor in yaml.load(Path(__file__).parent / "sensors.yaml")["sensors"]:

        config_description = sensor["description"]
        sensor_id = config_description["id"]
        identification = SensorIdentification(
            id=sensor_id,
            name=config_description["name"],
            type=config_description["type"],
        )

        coefficients = sensor["coefficients"]

        config_range = sensor["physical"]
        sensor_range = SensorRange(
            min=config_range["min"],
            max=config_range["max"],
            unit=ureg.parse_units(config_range["unit"]),
        )

        sensors[sensor_id] = Sensor(identification, coefficients, sensor_range)

    return sensors


# -- Classes ------------------------------------------------------------------


class SensorIdentification(NamedTuple):
    """Textual data about a specific sensor"""

    id: str
    """Unique text that identifies this sensor"""

    name: str
    """Human readable name for sensor"""

    type: str
    """Type of sensor e.g. “ADXL1001”"""


class SensorRange(NamedTuple):
    """Physical range of sensor values"""

    min: float
    """Minimum physical value of a sensor"""

    max: float
    """Maximum physical value of a sensor"""

    unit: Quantity
    """The physical unit of the min and max value"""


class Sensor:
    """Base class for a general sensor

    Args:

        identification:

            Textual data about the specific sensor

        coefficients:

            Polynomial coefficients for mapping from value range 0 to 1 to
            physical value

        sensor_range:

            The minimum and maximum physical values of the sensor

    Examples:

        Import required libraries

        >>> from math import isclose
        >>> from iconversion import g0

        Create a ±100g sensor

        >>> identification = SensorIdentification(
        ...     id="acc100g_01",
        ...     name="Acceleration 100g",
        ...     type="ADXL1001",
        ... )
        >>> coefficients=[
        ...     -125,
        ...     250,
        ... ]
        >>> sensor_range = SensorRange(
        ...     min=-125,
        ...     max=125,
        ...     unit=g0,
        ... )
        >>> sensor_100g = Sensor(
        ...     identification=identification,
        ...     coefficients=coefficients,
        ...     sensor_range=sensor_range,
        ... )

    """

    def __init__(
        self,
        identification: SensorIdentification,
        coefficients: list[float],
        sensor_range: SensorRange,
    ) -> None:
        self.identification = identification
        self.polynomial = Polynomial(coefficients)
        self.range = sensor_range
        self.unit = sensor_range.unit

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

            >>> identification = SensorIdentification(
            ...     id="acc100g_01",
            ...     name="Acceleration 100g",
            ...     type="ADXL1001",
            ... )
            >>> coefficients=[
            ...     -125,
            ...     250,
            ... ]
            >>> sensor_range = SensorRange(
            ...     min=-125,
            ...     max=125,
            ...     unit=g0,
            ... )
            >>> sensor_100g = Sensor(
            ...     identification=identification,
            ...     coefficients=coefficients,
            ...     sensor_range=sensor_range,
            ... )

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
            >>> isclose(min_100g, -125)
            True

            >>> max_16_bit = ADC_MAX_VALUE
            >>> max_100g = sensor_100g.convert(max_16_bit)
            >>> isclose(max_100g, 125)
            True

        """

        normalized_value = raw / ADC_MAX_VALUE
        physical_value = self.polynomial(normalized_value)

        return physical_value

    def __repr__(self):
        """Get the string representation of the sensor

        Returns:

            A text representing this sensor

        Examples:

            Import required libraries

            >>> from iconversion import degree_Celsius, g0

            Print representation of a temperature sensor

            >>> identification = SensorIdentification(
            ...     id="temp_01",
            ...     name="Temperature",
            ...     type="ADXL358C",
            ... )
            >>> coefficients=[
            ...     25 - 1100 * 0.976/3.3, # -300.3333333333333
            ...     330/0.3,               # 1100
            ... ]
            >>> sensor_range = SensorRange(
            ...     min=-40,
            ...     max=125,
            ...     unit=degree_Celsius,
            ... )

            >>> Sensor(
            ...     identification=identification,
            ...     coefficients=coefficients,
            ...     sensor_range=sensor_range,
            ... )
            Temperature [-40 °C, 125 °C] (-300.33333333 + 1100.0·x)

            Print representation of a ±100g acceleration sensor

            >>> identification = SensorIdentification(
            ...     id="acc100g_01",
            ...     name="Acceleration 100g",
            ...     type="ADXL1001",
            ... )
            >>> coefficients=[
            ...     -125,
            ...     250,
            ... ]
            >>> sensor_range = SensorRange(
            ...     min=-125,
            ...     max=125,
            ...     unit=g0,
            ... )
            >>> Sensor(
            ...     identification=identification,
            ...     coefficients=coefficients,
            ...     sensor_range=sensor_range,
            ... )
            Acceleration 100g [-125 g_0, 125 g_0] (-125.0 + 250.0·x)

        """

        polynomial = self.polynomial
        sensor_range = self.range
        unit = self.range.unit
        name = self.identification.name
        representation = (
            f"{name} [{sensor_range.min} {unit:~P}, {sensor_range.max} "
            f"{unit:~P}] ({polynomial:unicode})"
        )

        return representation
