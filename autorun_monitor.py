
import json
import winreg
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
BASELINE_FILE = PROJECT_DIR / "autorun_baseline.json"
LOG_FILE = PROJECT_DIR / "logs" / "autorun_changes.jsonl"

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
    if not BASELINE_FILE.exists():
        print("ERROR: Create autorun_baseline.json first.")
        return

    with BASELINE_FILE.open("r", encoding="utf-8") as file:
        baseline = json.load(file)["keys"]

    changes = []

    for hive, path, label in REGISTRY_KEYS:
        full_path = label + "\\" + path
        old_values = baseline.get(full_path)

        if old_values is None:
            print(f"WARNING: No baseline for {full_path}")
            continue

        current_values = read_values(hive, path)

        if current_values is None:
            print(f"WARNING: Key missing: {full_path}")
            continue

        all_names = sorted(set(old_values) | set(current_values))

        for name in all_names:
            old = old_values.get(name)
            new = current_values.get(name)

            if old is None:
                status = "ADDED"
            elif new is None:
                status = "DELETED"
            elif old != new:
                status = "MODIFIED"
            else:
                continue

            change = {
                "timestamp": datetime.now().astimezone().isoformat(),
                "status": status,
                "registry_path": full_path,
                "name": name,
                "old_value": old,
                "new_value": new
            }

            changes.append(change)

    if not changes:
        print("No changes detected.")
        return

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        for change in changes:
            file.write(json.dumps(change) + "\n")
            print(
                f'{change["status"]}: '
                f'{change["registry_path"]}\\{change["name"]}'
            )
            print(f'  Old: {change["old_value"]}')
            print(f'  New: {change["new_value"]}')

    print(f"\nLogged {len(changes)} change(s).")


if __name__ == "__main__":
    main()
