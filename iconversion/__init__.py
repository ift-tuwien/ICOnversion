"""Main module of conversion library"""

# -- Imports ------------------------------------------------------------------

from pint import UnitRegistry

# -- Exports ------------------------------------------------------------------

# Global registry for unit conversion

ureg: UnitRegistry = UnitRegistry()
g0 = ureg.g0
