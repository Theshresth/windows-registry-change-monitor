import winreg
import json
from pathlib import Path
from datetime import datetime

# Project configuration
REGISTRY_PATH = r"Software\RegistryMonitorLab"
BASELINE_FILE = Path(__file__).parent / "baseline.json"


def read_registry():
    """Read values from our dedicated test registry key."""
    data = {}

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        ) as key:

            value_count = winreg.QueryInfoKey(key)[1]

            for index in range(value_count):
                name, value, value_type = winreg.EnumValue(key, index)

                data[name] = {
                    "value": value,
                    "type": value_type
                }

    except FileNotFoundError:
        print("Test registry key not found.")
        print("Create the test key before running this script.")
        return None

    return data


def create_baseline():
    """Save the current registry state as our baseline."""
    registry_data = read_registry()

    if registry_data is None:
        return

    baseline = {
        "registry_path": (
            r"HKEY_CURRENT_USER\\" + REGISTRY_PATH
        ),
        "captured_at": datetime.now().astimezone().isoformat(),
        "values": registry_data
    }

    with BASELINE_FILE.open("w", encoding="utf-8") as file:
        json.dump(baseline, file, indent=4)

    print("Baseline created successfully!")
    print(f"Registry values captured: {len(registry_data)}")
    print(f"Saved to: {BASELINE_FILE}")


if __name__ == "__main__":
    create_baseline()