
import json
import winreg
from pathlib import Path
from datetime import datetime

BASELINE_FILE = Path(__file__).parent / "autorun_baseline.json"

REGISTRY_KEYS = [
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\Run",
     "HKCU"),
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
     "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\Run",
     "HKLM"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
     "HKLM"),
]


def read_values(hive, path):
    values = {}

    try:
        with winreg.OpenKey(
            hive, path, 0, winreg.KEY_READ
        ) as key:
            count = winreg.QueryInfoKey(key)[1]

            for index in range(count):
                name, value, value_type = winreg.EnumValue(
                    key, index
                )
                values[name] = {
                    "value": value,
                    "type": value_type
                }

        return values

    except FileNotFoundError:
        return None


def main():
    snapshot = {}

    for hive, path, label in REGISTRY_KEYS:
        full_path = label + "\\" + path
        values = read_values(hive, path)

        if values is None:
            print(f"Key not found: {full_path}")
            continue

        snapshot[full_path] = values
        print(f"Read {len(values)} value(s): {full_path}")

    data = {
        "created_at": datetime.now().astimezone().isoformat(),
        "keys": snapshot
    }

    with BASELINE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"\nBaseline saved to: {BASELINE_FILE}")
    print(f"Registry keys captured: {len(snapshot)}")


if __name__ == "__main__":
    main()
