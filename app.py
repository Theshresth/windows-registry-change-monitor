import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import threading
import queue
import json
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "lab_changes.jsonl"

REG_PATH = r"Software\RegistryMonitorLab"
TEST_VALUE = "DemoTest"
POLL_INTERVAL = 2


class RegistryMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Registry Change Monitor")
        self.root.geometry("780x570")

        self.running = False
        self.stop_event = threading.Event()
        self.output_queue = queue.Queue()
        self.monitor_thread = None
        self.previous_state = {}

        self.create_registry_key()

        ttk.Label(
            root,
            text="Windows Registry Change Monitor",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=12)

        ttk.Label(
            root,
            text="Safe interactive testing: HKCU\\Software\\RegistryMonitorLab"
        ).pack(pady=3)

        controls = ttk.Frame(root)
        controls.pack(pady=12)

        self.start_button = ttk.Button(
            controls, text="Start Monitoring",
            command=self.start_monitoring
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            controls, text="Stop Monitoring",
            command=self.stop_monitoring,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        ttk.Separator(root).pack(fill="x", padx=15, pady=8)

        ttk.Label(
            root,
            text="Interactive Test Controls",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=5)

        test_controls = ttk.Frame(root)
        test_controls.pack(pady=8)

        ttk.Button(
            test_controls, text="Add Test Value",
            command=self.add_test_value
        ).pack(side="left", padx=5)

        ttk.Button(
            test_controls, text="Modify Test Value",
            command=self.modify_test_value
        ).pack(side="left", padx=5)

        ttk.Button(
            test_controls, text="Delete Test Value",
            command=self.delete_test_value
        ).pack(side="left", padx=5)

        self.status = tk.StringVar(value="Status: Stopped")
        ttk.Label(
            root, textvariable=self.status,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=5)

        ttk.Label(
            root, text="Monitoring Output",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=5)

        self.output = tk.Text(root, wrap="word", height=17)
        self.output.pack(fill="both", expand=True, padx=15, pady=8)

        self.output.insert(
            "end",
            "Ready. Start monitoring, then use the test buttons.\n"
        )
        self.output.configure(state="disabled")

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.root.after(200, self.read_output)

    def create_registry_key(self):
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE
        ):
            pass

    def get_registry_state(self):
        state = {}

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                index = 0

                while True:
                    try:
                        name, value, value_type = winreg.EnumValue(
                            key, index
                        )
                        state[name] = {
                            "value": value,
                            "type": value_type
                        }
                        index += 1
                    except OSError:
                        break

        except FileNotFoundError:
            pass

        return state

    def write_log(self, event):
        LOG_DIR.mkdir(exist_ok=True)

        record = {
            "timestamp": datetime.now().isoformat(),
            "registry_path": "HKCU\\" + REG_PATH,
            **event
        }

        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

    def append_output(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def start_monitoring(self):
        if self.running:
            return

        self.previous_state = self.get_registry_state()
        self.stop_event.clear()
        self.running = True

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set("Status: Monitoring")

        self.append_output(
            "\nMonitoring started. Polling every 2 seconds.\n"
        )

        self.monitor_thread = threading.Thread(
            target=self.monitor_registry,
            daemon=True
        )
        self.monitor_thread.start()

    def monitor_registry(self):
        while not self.stop_event.is_set():
            try:
                current_state = self.get_registry_state()

                old_names = set(self.previous_state)
                new_names = set(current_state)

                for name in new_names - old_names:
                    self.report_change(
                        "ADDED", name, None,
                        current_state[name]["value"]
                    )

                for name in old_names - new_names:
                    self.report_change(
                        "DELETED", name,
                        self.previous_state[name]["value"], None
                    )

                for name in old_names & new_names:
                    old_value = self.previous_state[name]["value"]
                    new_value = current_state[name]["value"]

                    if old_value != new_value:
                        self.report_change(
                            "MODIFIED", name, old_value, new_value
                        )

                self.previous_state = current_state

            except Exception as error:
                self.output_queue.put(
                    f"Monitoring error: {error}\n"
                )

            self.stop_event.wait(POLL_INTERVAL)

        self.output_queue.put("__STOPPED__")

    def report_change(self, action, name, old_value, new_value):
        event = {
            "action": action,
            "value_name": name,
            "old_value": old_value,
            "new_value": new_value
        }

        try:
            self.write_log(event)
        except OSError as error:
            self.output_queue.put(f"Log error: {error}\n")

        self.output_queue.put(
            f"{action}: {name} | Old: {old_value} | New: {new_value}\n"
        )

    def add_test_value(self):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key, TEST_VALUE, 0,
                    winreg.REG_SZ, "Initial Test Value"
                )

            self.append_output(
                "Test value created/updated: " + TEST_VALUE + "\n"
            )

        except OSError as error:
            messagebox.showerror("Registry Error", str(error))

    def modify_test_value(self):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key, TEST_VALUE, 0,
                    winreg.REG_SZ, "Modified Test Value"
                )

            self.append_output(
                "Test value modification requested.\n"
            )

        except OSError as error:
            messagebox.showerror("Registry Error", str(error))

    def delete_test_value(self):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, TEST_VALUE)

            self.append_output(
                "Test value deletion requested.\n"
            )

        except FileNotFoundError:
            messagebox.showinfo(
                "Not Found", "DemoTest does not exist."
            )
        except OSError as error:
            messagebox.showerror("Registry Error", str(error))

    def stop_monitoring(self):
        if self.running:
            self.stop_event.set()
            self.status.set("Status: Stopping...")

    def read_output(self):
        while not self.output_queue.empty():
            item = self.output_queue.get()

            if item == "__STOPPED__":
                self.running = False
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.status.set("Status: Stopped")
                self.append_output("Monitoring stopped.\n")
            else:
                self.append_output(item)

        self.root.after(200, self.read_output)

    def close_app(self):
        self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RegistryMonitorApp(root)
    root.mainloop()
