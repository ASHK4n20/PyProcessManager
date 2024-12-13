#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import psutil
from process_manager import ProcessManager
import time
import threading

class ProcessListGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PyProcessManager - Process List")
        self.root.geometry("800x600")
        
        # Create ProcessManager instance
        self.pm = ProcessManager()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create treeview
        self.tree = ttk.Treeview(self.main_frame, columns=("Status", "PID", "CPU", "Memory", "AutoRun"), show="headings")
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column headings
        self.tree.heading("Status", text="Status")
        self.tree.heading("PID", text="PID")
        self.tree.heading("CPU", text="CPU %")
        self.tree.heading("Memory", text="Memory MB")
        self.tree.heading("AutoRun", text="Auto-Run")
        
        # Configure column widths
        self.tree.column("Status", width=100)
        self.tree.column("PID", width=100)
        self.tree.column("CPU", width=100)
        self.tree.column("Memory", width=100)
        self.tree.column("AutoRun", width=100)
        
        # Add buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Start", command=self.start_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop", command=self.stop_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Restart", command=self.restart_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Logs", command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

    def get_process_stats(self, pid):
        try:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.1)
            mem = process.memory_info().rss / 1024 / 1024  # Convert to MB
            return cpu, mem
        except:
            return 0, 0

    def update_process_list(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add processes
        for title, info in self.pm.processes.items():
            status = info['status']
            pid = info['pid'] or ''
            cpu = 'N/A'
            mem = 'N/A'
            
            if status == 'running' and pid:
                try:
                    cpu_usage, mem_usage = self.get_process_stats(pid)
                    cpu = f"{cpu_usage:.1f}"
                    mem = f"{mem_usage:.1f}"
                except:
                    pass
            
            autorun = '✓' if info['autorun'] else '✗'
            
            # Insert with tag for color
            tags = ('running',) if status == 'running' else ('stopped',)
            self.tree.insert('', tk.END, text=title, values=(status, pid, cpu, mem, autorun), tags=tags)
        
        # Configure tags for colors
        self.tree.tag_configure('running', foreground='green')
        self.tree.tag_configure('stopped', foreground='red')

    def update_loop(self):
        while self.running:
            self.update_process_list()
            time.sleep(2)

    def get_selected_process(self):
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        return item.get('text')  # Get the title

    def start_process(self):
        title = self.get_selected_process()
        if title:
            self.pm.start(title)

    def stop_process(self):
        title = self.get_selected_process()
        if title:
            self.pm.stop(title)

    def restart_process(self):
        title = self.get_selected_process()
        if title:
            self.pm.stop(title)
            time.sleep(1)
            self.pm.start(title)

    def view_logs(self):
        title = self.get_selected_process()
        if title:
            import subprocess
            import os
            
            log_dir = os.path.join(self.pm.config_dir, 'logs')
            stdout_log = os.path.join(log_dir, f"{title}.out")
            stderr_log = os.path.join(log_dir, f"{title}.err")
            
            # Open logs with default text editor
            if os.path.exists(stdout_log):
                subprocess.Popen(['xdg-open', stdout_log])
            if os.path.exists(stderr_log):
                subprocess.Popen(['xdg-open', stderr_log])

    def on_closing(self):
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ProcessListGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
