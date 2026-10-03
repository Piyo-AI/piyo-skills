"""Converts a value between units. Reads one JSON object on stdin, prints one JSON object on stdout.

Input:  {"value": 5, "from": "mi", "to": "km"}
Output: {"result": 8.04672, "text": "5 mi = 8.04672 km"}  or  {"error": "..."}
"""

import json
import sys

# Each group maps a unit to the size of one unit in the group's base unit.
GROUPS = {
    "length": {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344},
    "mass": {"mg": 1e-6, "g": 0.001, "kg": 1.0, "oz": 0.028349523125, "lb": 0.45359237},
    "volume": {
        "ml": 0.001, "l": 1.0, "tsp": 0.00492892159375, "tbsp": 0.01478676478125,
        "cup": 0.2365882365, "floz": 0.0295735295625, "gal": 3.785411784,
    },
}
TEMPERATURE = {"c", "f", "k"}


def to_celsius(value: float, unit: str) -> float:
    return {"c": value, "f": (value - 32) * 5 / 9, "k": value - 273.15}[unit]


def from_celsius(value: float, unit: str) -> float:
    return {"c": value, "f": value * 9 / 5 + 32, "k": value + 273.15}[unit]


def convert(value: float, source: str, target: str) -> float:
    if source in TEMPERATURE and target in TEMPERATURE:
        celsius = to_celsius(value, source)
        if celsius < -273.15 - 1e-9:
            raise ValueError("That is below absolute zero.")
        return from_celsius(celsius, target)
    for group, units in GROUPS.items():
        if source in units and target in units:
            return value * units[source] / units[target]
    known = set(TEMPERATURE).union(*GROUPS.values())
    for unit in (source, target):
        if unit not in known:
            raise ValueError(f"Unknown unit {unit!r}.")
    raise ValueError(f"{source} and {target} measure different things.")


def main() -> None:
    try:
        data = json.load(sys.stdin)
        value = float(data["value"])
        source, target = str(data["from"]).strip().lower(), str(data["to"]).strip().lower()
        result = round(convert(value, source, target), 6)
        shown = int(result) if result == int(result) else result
        given = int(value) if value == int(value) else value
        print(json.dumps({"result": shown, "text": f"{given} {source} = {shown} {target}"}))
    except (KeyError, TypeError):
        print(json.dumps({"error": "Give value (a number), from and to."}))
    except ValueError as e:
        print(json.dumps({"error": str(e)}))


main()
