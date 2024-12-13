#!/usr/bin/env python3
from blessed import Terminal
import psutil
import time
import threading
import os
from process_manager import ProcessManager
import sys
from collections import deque

class ProcessManagerTUI:
    def __init__(self):
        self.term = Terminal()
        self.pm = ProcessManager()
        self.selected_index = 0
        self.view_mode = 'processes'  # 'processes', 'logs', 'add'
        self.running = True
        self.log_lines = deque(maxlen=1000)
        self.current_log_process = None
        self.command_buffer = ""
        self.add_process_fields = {
            'name': '',
            'command': '',
            'autorun': False
        }
        self.add_process_field_index = 0
        self.status_message = ""
        self.status_time = 0

    def show_status(self, message, duration=3):
        """Show a status message for a few seconds"""
        self.status_message = message
        self.status_time = time.time() + duration

    def clear_status(self):
        """Clear the status message if it's expired"""
        if self.status_message and time.time() > self.status_time:
            self.status_message = ""

    def get_process_stats(self, pid):
        """Get CPU and memory stats for a process"""
        try:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.1)
            mem = process.memory_info().rss / 1024 / 1024  # Convert to MB
            return cpu, mem
        except:
            return 0, 0

    def draw_processes(self):
        """Draw the process list view"""
        processes = list(self.pm.processes.items())
        if not processes:
            print(self.term.center('No processes found. Press "a" to add a new process.'))
            return

        # Header
        print(self.term.black_on_white(self.term.center(
            f"{'Name':<20} {'Status':<10} {'PID':<8} {'CPU %':<8} {'MEM MB':<8} {'Auto':<6}"
        )))
        
        # Process list
        for i, (title, info) in enumerate(processes):
            if i >= self.term.height - 8:  # Leave room for header and footer
                break
                
            selected = i == self.selected_index
            status = info['status']
            pid = info['pid'] or 'N/A'
            
            cpu = 'N/A'
            mem = 'N/A'
            if status == 'running' and pid != 'N/A':
                try:
                    cpu_usage, mem_usage = self.get_process_stats(pid)
                    cpu = f"{cpu_usage:.1f}"
                    mem = f"{mem_usage:.1f}"
                except:
                    pass
            
            line = f"{title:<20} {status:<10} {str(pid):<8} {cpu:<8} {mem:<8} {'✓' if info['autorun'] else '✗':<6}"
            
            if selected:
                if status == 'running':
                    print(self.term.black_on_green(line))
                else:
                    print(self.term.black_on_red(line))
            else:
                if status == 'running':
                    print(self.term.green(line))
                else:
                    print(self.term.red(line))

    def draw_logs(self):
        """Draw the log viewer"""
        if not self.current_log_process:
            print(self.term.center('No process selected for logs. Press ESC to go back and select a process.'))
            return

        # Header
        print(self.term.black_on_white(self.term.center(f"Logs for: {self.current_log_process}")))
        
        # Read logs
        log_dir = os.path.join(self.pm.config_dir, 'logs')
        stdout_log = os.path.join(log_dir, f"{self.current_log_process}.out")
        stderr_log = os.path.join(log_dir, f"{self.current_log_process}.err")
        
        try:
            # Show last N lines that fit in the terminal
            max_lines = self.term.height - 8
            
            # Read stdout
            if os.path.exists(stdout_log):
                with open(stdout_log, 'r') as f:
                    stdout_lines = f.readlines()[-max_lines:]
                    for line in stdout_lines:
                        print(self.term.white(line.strip()))
            
            # Read stderr
            if os.path.exists(stderr_log):
                with open(stderr_log, 'r') as f:
                    stderr_lines = f.readlines()[-max_lines:]
                    for line in stderr_lines:
                        print(self.term.red(line.strip()))
        except Exception as e:
            print(self.term.red(f"Error reading logs: {str(e)}"))

    def draw_add_process(self):
        """Draw the add process form"""
        print(self.term.black_on_white(self.term.center("Add New Process")))
        print()
        
        fields = [
            ('Process Name:', self.add_process_fields['name']),
            ('Command:', self.add_process_fields['command']),
            ('Auto-run:', '✓' if self.add_process_fields['autorun'] else '✗')
        ]
        
        for i, (label, value) in enumerate(fields):
            if i == self.add_process_field_index:
                print(self.term.black_on_white(f"{label:<15} {value}"))
            else:
                print(f"{label:<15} {value}")

    def draw_help(self):
        """Draw help based on current view"""
        help_text = ""
        
        if self.view_mode == 'processes':
            help_text = "↑/k,↓/j: Select | Enter/Space: Start/Stop | r: Restart | l: View Logs | a: Add | s: Setup Startup | q: Quit"
        elif self.view_mode == 'logs':
            help_text = "q/ESC: Back"
        elif self.view_mode == 'add':
            help_text = "↑/k,↓/j: Select Field | Enter: Next/Save | ESC: Cancel | Space: Toggle Auto-run"
            
        print(self.term.move(self.term.height-2, 0) + self.term.black_on_white(self.term.center(help_text)))

    def draw_status(self):
        """Draw status message if any"""
        if self.status_message:
            print(self.term.move(self.term.height-3, 0) + self.term.center(self.term.yellow(self.status_message)))

    def draw(self):
        """Main draw function"""
        print(self.term.clear)
        
        # Title
        print(self.term.black_on_white(self.term.center("PyProcessManager")))
        print()
        
        # Main content
        if self.view_mode == 'processes':
            self.draw_processes()
        elif self.view_mode == 'logs':
            self.draw_logs()
        elif self.view_mode == 'add':
            self.draw_add_process()
            
        # Status and Help
        self.draw_status()
        self.draw_help()

    def handle_processes_input(self, key):
        """Handle input in processes view"""
        processes = list(self.pm.processes.items())
        if not processes:
            if key == 'a':
                self.view_mode = 'add'
            elif key == 'q':
                self.running = False
            return

        # Support both arrow keys and k/j for navigation
        if key in ('KEY_UP', 'k', 'K') and self.selected_index > 0:
            self.selected_index -= 1
        elif key in ('KEY_DOWN', 'j', 'J') and self.selected_index < len(processes) - 1:
            self.selected_index += 1
        elif key in ('KEY_ENTER', '\n', ' '):  # Support both Enter and Space
            title = processes[self.selected_index][0]
            if processes[self.selected_index][1]['status'] == 'running':
                self.pm.stop(title)
                self.show_status(f"Stopped process: {title}")
            else:
                self.pm.start(title)
                self.show_status(f"Started process: {title}")
        elif key in ('r', 'R'):
            title = processes[self.selected_index][0]
            self.pm.stop(title)
            time.sleep(1)
            self.pm.start(title)
            self.show_status(f"Restarted process: {title}")
        elif key in ('l', 'L'):
            self.current_log_process = processes[self.selected_index][0]
            self.view_mode = 'logs'
        elif key in ('a', 'A'):
            self.view_mode = 'add'
            self.add_process_fields = {'name': '', 'command': '', 'autorun': False}
            self.add_process_field_index = 0
        elif key in ('s', 'S'):
            self.pm.setup_startup()
            self.show_status("Setup startup processes")
        elif key in ('q', 'Q'):
            self.running = False

    def handle_logs_input(self, key):
        """Handle input in logs view"""
        if key in ('KEY_ESCAPE', 'q', 'Q', '\x1b'):  # Support Esc, q and Q
            self.view_mode = 'processes'
            self.current_log_process = None

    def handle_add_input(self, key):
        """Handle input in add process view"""
        if key in ('KEY_ESCAPE', '\x1b'):  # Support Esc key
            self.view_mode = 'processes'
        elif key in ('KEY_UP', 'k', 'K') and self.add_process_field_index > 0:
            self.add_process_field_index -= 1
        elif key in ('KEY_DOWN', 'j', 'J') and self.add_process_field_index < 2:
            self.add_process_field_index += 1
        elif key == ' ' and self.add_process_field_index == 2:
            # Toggle autorun
            self.add_process_fields['autorun'] = not self.add_process_fields['autorun']
        elif key in ('KEY_ENTER', '\n'):
            if self.add_process_field_index < 2:
                self.add_process_field_index += 1
            else:
                # Try to save the process
                name = self.add_process_fields['name'].strip()
                command = self.add_process_fields['command'].strip()
                if name and command:
                    try:
                        self.pm.save(name, command, os.getcwd(), self.add_process_fields['autorun'])
                        self.show_status(f"Added process: {name}")
                        self.view_mode = 'processes'
                    except Exception as e:
                        self.show_status(f"Error: {str(e)}")
                else:
                    self.show_status("Please fill in all fields")
        elif key in ('KEY_BACKSPACE', '\x7f', '\b'):  # Support different backspace codes
            # Handle backspace
            if self.add_process_field_index == 0:
                self.add_process_fields['name'] = self.add_process_fields['name'][:-1]
            elif self.add_process_field_index == 1:
                self.add_process_fields['command'] = self.add_process_fields['command'][:-1]
        elif key.isprintable():
            # Add printable characters to fields
            if self.add_process_field_index == 0:
                self.add_process_fields['name'] += key
            elif self.add_process_field_index == 1:
                self.add_process_fields['command'] += key

    def run(self):
        """Main run loop"""
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            while self.running:
                # Draw the UI
                self.draw()
                self.clear_status()
                
                # Handle input
                key = self.term.inkey(timeout=1)
                if key:
                    if self.view_mode == 'processes':
                        self.handle_processes_input(key)
                    elif self.view_mode == 'logs':
                        self.handle_logs_input(key)
                    elif self.view_mode == 'add':
                        self.handle_add_input(key)

def main():
    app = ProcessManagerTUI()
    app.run()

if __name__ == "__main__":
    main()
