
import json
import winreg
from pathlib import Path
from datetime import datetime

REGISTRY_PATH = r"Software\RegistryMonitorLab"
BASELINE_FILE = Path(__file__).parent / "baseline.json"
LOG_FILE = Path(__file__).parent / "logs" / "changes.jsonl"


def read_registry():
    values = {}

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        ) as key:
            count = winreg.QueryInfoKey(key)[1]

            for index in range(count):
                name, value, value_type = winreg.EnumValue(key, index)
                values[name] = {
                    "value": value,
                    "type": value_type
                }

    except FileNotFoundError:
        print("ERROR: Test registry key not found.")
        return None

    return values


def main():
    if not BASELINE_FILE.exists():
        print("ERROR: Create baseline.json first.")
        return

    with BASELINE_FILE.open("r", encoding="utf-8") as file:
        baseline = json.load(file)["values"]

    current = read_registry()

    if current is None:
        return

    changes = []

    for name in sorted(set(baseline) | set(current)):
        old = baseline.get(name)
        new = current.get(name)

        if old is None:
            status = "ADDED"
        elif new is None:
            status = "DELETED"
        elif old != new:
            status = "MODIFIED"
        else:
            continue

        changes.append({
            "timestamp": datetime.now().astimezone().isoformat(),
            "status": status,
            "name": name,
            "old_value": old,
            "new_value": new
        })

    if not changes:
        print("No changes detected.")
        return

    with LOG_FILE.open("a", encoding="utf-8") as file:
        for change in changes:
            file.write(json.dumps(change) + "\n")
            print(
                f'{change["status"]}: {change["name"]} '
                f'| Old: {change["old_value"]} '
                f'| New: {change["new_value"]}'
            )

    print(f"Logged {len(changes)} change(s).")


if __name__ == "__main__":
    main()
