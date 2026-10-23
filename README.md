# Windows Registry Change Monitoring System

## Project Overview
A Python-based cybersecurity project that monitors Windows Registry changes, compares registry data against a saved baseline, verifies baseline integrity using SHA-256, and analyzes autorun entries using basic suspicious-indicator rules.

## Features
- Registry baseline creation and comparison
- Detection of added, modified, and deleted registry values
- SHA-256 baseline integrity verification
- Monitoring of registry changes in a dedicated test lab key
- Basic heuristic analysis of autorun entries
- JSON and JSONL logging for investigation and reporting

## Project Files
- `baseline.py` — creates the registry baseline
- `monitor.py` — compares current registry data with the baseline
- `autorun_baseline.py` — captures autorun entries
- `autorun_monitor.py` — compares current autorun entries with a saved baseline
- `autorun_watch.py` — watches for autorun changes
- `lab_watch.py` — monitors the dedicated registry test key
- `suspicious_analyzer.py` — flags entries matching basic suspicious indicators

## Technologies
- Python
- Windows Registry
- SHA-256
- JSON / JSONL
- Windows command line

## Testing
The dedicated lab registry key was used to test added, modified, and deleted registry values. Baseline integrity verification and basic autorun-entry analysis were also tested.

## Limitations
The suspicious-indicator analyzer is heuristic-based and may produce false positives or miss threats. A clean result does not prove a system is malware-free. Local baseline and hash files are not protected against an attacker who can modify both.

## Disclaimer
This project is intended for educational cybersecurity learning and authorized testing only. Use a dedicated lab registry key for testing.
