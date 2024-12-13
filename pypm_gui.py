#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext
import psutil
from process_manager import ProcessManager
import time
import threading
import os
import subprocess
from tkinter import messagebox

class PyPMGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PyProcessManager")
        self.root.geometry("1000x700")
        
        # Create ProcessManager instance
        self.pm = ProcessManager()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_process_tab()
        self.create_logs_tab()
        self.create_add_process_tab()
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_process_tab(self):
        """Create the processes list tab"""
        process_frame = ttk.Frame(self.notebook)
        self.notebook.add(process_frame, text='Processes')
        
        # Create treeview
        self.tree = ttk.Treeview(process_frame, columns=("Status", "PID", "CPU", "Memory", "AutoRun"), show="headings")
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.tree.heading("Status", text="Status")
        self.tree.heading("PID", text="PID")
        self.tree.heading("CPU", text="CPU %")
        self.tree.heading("Memory", text="Memory MB")
        self.tree.heading("AutoRun", text="Auto-Run")
        
        for col in ("Status", "PID", "CPU", "Memory", "AutoRun"):
            self.tree.column(col, width=100)
        
        # Add control buttons
        btn_frame = ttk.Frame(process_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Start", command=self.start_process).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Stop", command=self.stop_process).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Restart", command=self.restart_process).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="View Logs", command=self.view_process_logs).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Toggle Auto-Run", command=self.toggle_autorun).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Setup Startup", command=self.setup_startup).pack(side='left', padx=2)

    def create_logs_tab(self):
        """Create the log viewer tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text='Logs')
        
        # Process selector
        self.log_process_var = tk.StringVar()
        selector_frame = ttk.Frame(logs_frame)
        selector_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(selector_frame, text="Process:").pack(side='left', padx=5)
        self.process_combo = ttk.Combobox(selector_frame, textvariable=self.log_process_var)
        self.process_combo.pack(side='left', padx=5)
        
        ttk.Button(selector_frame, text="Refresh", command=self.refresh_logs).pack(side='left', padx=5)
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(selector_frame, text="Auto-refresh", variable=self.auto_refresh_var).pack(side='left', padx=5)
        
        # Log viewer
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=30)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

    def create_add_process_tab(self):
        """Create the add process tab"""
        add_frame = ttk.Frame(self.notebook)
        self.notebook.add(add_frame, text='Add Process')
        
        # Form fields
        form_frame = ttk.Frame(add_frame)
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        ttk.Label(form_frame, text="Process Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.title_entry = ttk.Entry(form_frame, width=50)
        self.title_entry.grid(row=0, column=1, sticky='w', pady=5)
        
        # Command
        ttk.Label(form_frame, text="Command:").grid(row=1, column=0, sticky='w', pady=5)
        self.command_entry = ttk.Entry(form_frame, width=50)
        self.command_entry.grid(row=1, column=1, sticky='w', pady=5)
        
        # Working Directory
        ttk.Label(form_frame, text="Working Directory:").grid(row=2, column=0, sticky='w', pady=5)
        self.cwd_entry = ttk.Entry(form_frame, width=50)
        self.cwd_entry.insert(0, os.getcwd())  # Default to current directory
        self.cwd_entry.grid(row=2, column=1, sticky='w', pady=5)
        
        # Auto-run
        self.autorun_var = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="Auto-run on startup", variable=self.autorun_var).grid(row=3, column=1, sticky='w', pady=5)
        
        # Add button
        ttk.Button(form_frame, text="Add Process", command=self.add_process).grid(row=4, column=1, sticky='w', pady=20)

    def get_process_stats(self, pid):
        """Get CPU and memory stats for a process"""
        try:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.1)
            mem = process.memory_info().rss / 1024 / 1024  # Convert to MB
            return cpu, mem
        except:
            return 0, 0

    def update_process_list(self):
        """Update the process list in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Update process combo in logs tab
        process_titles = list(self.pm.processes.keys())
        self.process_combo['values'] = process_titles
        
        # Add processes to treeview
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

    def update_logs(self):
        """Update the log viewer"""
        if not self.auto_refresh_var.get():
            return
            
        title = self.log_process_var.get()
        if not title:
            return
            
        log_dir = os.path.join(self.pm.config_dir, 'logs')
        stdout_log = os.path.join(log_dir, f"{title}.out")
        stderr_log = os.path.join(log_dir, f"{title}.err")
        
        log_content = ""
        
        if os.path.exists(stdout_log):
            with open(stdout_log, 'r') as f:
                log_content += "=== STDOUT ===\n"
                log_content += f.read()
                log_content += "\n\n"
                
        if os.path.exists(stderr_log):
            with open(stderr_log, 'r') as f:
                log_content += "=== STDERR ===\n"
                log_content += f.read()
        
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, log_content)
        self.log_text.see(tk.END)  # Scroll to bottom

    def update_loop(self):
        """Background update loop"""
        while self.running:
            self.update_process_list()
            self.update_logs()
            time.sleep(2)

    def get_selected_process(self):
        """Get the selected process from the treeview"""
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        return item.get('text')

    def start_process(self):
        """Start the selected process"""
        title = self.get_selected_process()
        if title:
            self.pm.start(title)

    def stop_process(self):
        """Stop the selected process"""
        title = self.get_selected_process()
        if title:
            self.pm.stop(title)

    def restart_process(self):
        """Restart the selected process"""
        title = self.get_selected_process()
        if title:
            self.pm.stop(title)
            time.sleep(1)
            self.pm.start(title)

    def view_process_logs(self):
        """Switch to logs tab for selected process"""
        title = self.get_selected_process()
        if title:
            self.log_process_var.set(title)
            self.notebook.select(1)  # Switch to logs tab
            self.refresh_logs()

    def refresh_logs(self):
        """Force refresh logs"""
        self.update_logs()

    def toggle_autorun(self):
        """Toggle autorun for selected process"""
        title = self.get_selected_process()
        if title and title in self.pm.processes:
            current = self.pm.processes[title]['autorun']
            self.pm.processes[title]['autorun'] = not current
            self.pm._save_processes()
            self.update_process_list()

    def setup_startup(self):
        """Setup startup for autorun processes"""
        try:
            self.pm.setup_startup()
            messagebox.showinfo("Success", "Startup configuration completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to setup startup: {str(e)}")

    def add_process(self):
        """Add a new process"""
        title = self.title_entry.get().strip()
        command = self.command_entry.get().strip()
        cwd = self.cwd_entry.get().strip()
        autorun = self.autorun_var.get()
        
        if not title or not command:
            messagebox.showerror("Error", "Please provide both process name and command!")
            return
            
        try:
            self.pm.save(title, command, cwd, autorun)
            messagebox.showinfo("Success", f"Process '{title}' added successfully!")
            
            # Clear form
            self.title_entry.delete(0, tk.END)
            self.command_entry.delete(0, tk.END)
            self.autorun_var.set(False)
            
            # Switch to processes tab
            self.notebook.select(0)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add process: {str(e)}")

    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = PyPMGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
