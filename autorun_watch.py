
import json
import time
import winreg
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
BASELINE_FILE = PROJECT_DIR / "autorun_baseline.json"
STATE_FILE = PROJECT_DIR / "autorun_last_state.json"
LOG_FILE = PROJECT_DIR / "logs" / "autorun_changes.jsonl"

INTERVAL_SECONDS = 10

REGISTRY_KEYS = [
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM"),
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


def read_current_state():
    snapshot = {}

    for hive, path, label in REGISTRY_KEYS:
        full_path = label + "\\" + path
        values = read_values(hive, path)

        # Missing/unreadable keys are skipped, not treated as empty.
        if values is not None:
            snapshot[full_path] = values

    return snapshot


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump({"keys": state}, file, indent=2)


def compare_states(previous, current):
    changes = []

    for registry_path, new_values in current.items():
        old_values = previous.get(registry_path)

        if old_values is None:
            continue

        for name in sorted(set(old_values) | set(new_values)):
            old = old_values.get(name)
            new = new_values.get(name)

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
                "registry_path": registry_path,
                "name": name,
                "old_value": old,
                "new_value": new
            })

    return changes


def main():
    if not BASELINE_FILE.exists():
        print("ERROR: Create autorun_baseline.json first.")
        return

    baseline = load_json(BASELINE_FILE)["keys"]

    if STATE_FILE.exists():
        previous = load_json(STATE_FILE)["keys"]
        print("Loaded previous monitoring state.")
    else:
        previous = baseline.copy()
        save_state(previous)
        print("Initialized monitoring state from baseline.")

    print(f"Monitoring every {INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            current = read_current_state()
            changes = compare_states(previous, current)

            if changes:
                with LOG_FILE.open("a", encoding="utf-8") as file:
                    for change in changes:
                        file.write(json.dumps(change) + "\n")
                        print(
                            f'{change["status"]}: '
                            f'{change["registry_path"]}\\'
                            f'{change["name"]}'
                        )
                print(f"Detected {len(changes)} change(s).")
            else:
                print("No new changes detected.")

            # Update only keys successfully read this cycle.
            previous.update(current)
            save_state(previous)

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()
