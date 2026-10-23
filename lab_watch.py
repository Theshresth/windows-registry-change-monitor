
import winreg
import time
import json
from pathlib import Path
from datetime import datetime

REGISTRY_PATH = r"Software\RegistryMonitorLab"
LOG_FILE = Path(__file__).parent / "logs" / "lab_changes.jsonl"
INTERVAL = 5


def read_lab_key():
    values = {}

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        ) as key:
            count = winreg.QueryInfoKey(key)[1]

            for i in range(count):
                name, value, value_type = winreg.EnumValue(key, i)
                values[name] = {
                    "value": value,
                    "type": value_type
                }

    except FileNotFoundError:
        print("Lab registry key not found.")
        return None

    return values


def main():
    previous = read_lab_key()

    if previous is None:
        return

    print("Lab watcher started. Checking every 5 seconds.")
    print("Change a lab value to test detection.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            current = read_lab_key()

            if current is None:
                time.sleep(INTERVAL)
                continue

            changes = []

            for name in sorted(set(previous) | set(current)):
                old = previous.get(name)
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
                    "registry_path": "HKCU\\" + REGISTRY_PATH,
                    "name": name,
                    "old_value": old,
                    "new_value": new
                })

            if changes:
                with LOG_FILE.open("a", encoding="utf-8") as f:
                    for change in changes:
                        f.write(json.dumps(change) + "\n")
                        print(
                            f'{change["status"]}: {change["name"]}'
                        )
                        print(f'  Old: {change["old_value"]}')
                        print(f'  New: {change["new_value"]}')

            previous = current
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\nWatcher stopped.")


if __name__ == "__main__":
    main()
