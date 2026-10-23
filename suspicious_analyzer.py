
import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
BASELINE_FILE = PROJECT_DIR / "autorun_baseline.json"
REPORT_DIR = PROJECT_DIR / "reports"
REPORT_FILE = REPORT_DIR / "suspicious_analysis.json"

SCRIPT_TOOLS = (
    "powershell.exe",
    "wscript.exe",
    "cscript.exe",
    "mshta.exe",
)

SUSPICIOUS_LOCATIONS = (
    "\\appdata\\local\\temp\\",
    "\\windows\\temp\\",
    "\\downloads\\",
)


def analyze_entry(name, entry):
    command = str(entry.get("value", ""))
    text = command.lower()
    flags = []

    if any(tool in text for tool in SCRIPT_TOOLS):
        flags.append("Uses a script/command interpreter")

    if any(location in text for location in SUSPICIOUS_LOCATIONS):
        flags.append("References a user-writable location")

    if re.search(r"https?://", text):
        flags.append("Contains a URL in the command")

    if not command.strip():
        flags.append("Empty autorun command")

    # Simple review priority, not a malware verdict.
    if len(flags) >= 2:
        severity = "HIGH"
    elif len(flags) == 1:
        severity = "MEDIUM"
    else:
        severity = "NONE"

    return flags, severity


def main():
    if not BASELINE_FILE.exists():
        print("ERROR: autorun_baseline.json not found.")
        return

    with BASELINE_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    REPORT_DIR.mkdir(exist_ok=True)
    findings = []
    entries_found = 0

    for registry_path, entries in data["keys"].items():
        for name, entry in entries.items():
            entries_found += 1
            flags, severity = analyze_entry(name, entry)

            if flags:
                finding = {
                    "registry_path": registry_path,
                    "value_name": name,
                    "command": entry.get("value", ""),
                    "severity": severity,
                    "reasons": flags,
                }
                findings.append(finding)

                print(f"\nREVIEW [{severity}]: {registry_path}\\{name}")
                print(f"Command: {entry.get('value', '')}")

                for flag in flags:
                    print(f"  - {flag}")

    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": str(BASELINE_FILE.name),
        "entries_reviewed": entries_found,
        "entries_flagged": len(findings),
        "findings": findings,
        "note": "Heuristic indicators only; findings are not proof of malware."
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nAnalysis complete.")
    print(f"Entries reviewed: {entries_found}")
    print(f"Entries flagged: {len(findings)}")
    print(f"Report saved to: {REPORT_FILE}")
    print("Flags are indicators, not proof of malware.")


if __name__ == "__main__":
    main()

