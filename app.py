import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
from pathlib import Path
import threading
import queue

PROJECT_DIR = Path(__file__).parent
WATCHER = PROJECT_DIR / "autorun_watch.py"


class RegistryMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Registry Monitor")
        self.root.geometry("720x480")
        self.process = None
        self.output_queue = queue.Queue()

        ttk.Label(
            root,
            text="Windows Registry Change Monitor",
            font=("Segoe UI", 17, "bold")
        ).pack(pady=15)

        ttk.Label(
            root,
            text="Monitors startup registry entries in read-only mode."
        ).pack()

        controls = ttk.Frame(root)
        controls.pack(pady=12)

        self.start_button = ttk.Button(
            controls, text="Start Monitoring",
            command=self.start_monitoring
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            controls, text="Stop Monitoring",
            command=self.stop_monitoring, state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        self.status = tk.StringVar(value="Status: Stopped")
        ttk.Label(root, textvariable=self.status).pack(pady=5)

        self.output = tk.Text(root, wrap="word", height=17)
        self.output.pack(fill="both", expand=True, padx=15, pady=10)
        self.output.insert("end", "Ready. Click Start Monitoring.\n")
        self.output.configure(state="disabled")

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.root.after(200, self.read_output)

    def append_output(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def start_monitoring(self):
        if not WATCHER.exists():
            messagebox.showerror(
                "File not found",
                "autorun_watch.py was not found in the project folder."
            )
            return

        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", str(WATCHER)],
                cwd=str(PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
        except OSError as exc:
            messagebox.showerror("Could not start", str(exc))
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set("Status: Starting")
        threading.Thread(
            target=self.read_process,
            daemon=True
        ).start()

    def read_process(self):
        process = self.process
        if process is None or process.stdout is None:
            return

        for line in process.stdout:
            self.output_queue.put(line)

        process.wait()
        self.output_queue.put(
            f"\nWatcher exited with code {process.returncode}.\n"
        )
        self.output_queue.put("__STOPPED__")

    def read_output(self):
        while not self.output_queue.empty():
            line = self.output_queue.get()

            if line == "__STOPPED__":
                self.process = None
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.status.set("Status: Stopped")
            else:
                self.append_output(line)
                if "Monitoring every" in line:
                    self.status.set("Status: Monitoring")

        self.root.after(200, self.read_output)

    def stop_monitoring(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.status.set("Status: Stopping...")

    def close_app(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RegistryMonitorApp(root)
    root.mainloop()
