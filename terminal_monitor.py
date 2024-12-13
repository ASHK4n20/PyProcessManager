#!/usr/bin/env python3
from blessed import Terminal
import threading
import time
import os
import sys
from process_manager import ProcessManager
import signal
import psutil

class TerminalUI:
    def __init__(self):
        self.term = Terminal()
        self.pm = ProcessManager()
        self.selected_index = 0
        self.running = True
        self.process_list = []
        self.update_interval = 2  # seconds
        
        # Start the update thread
        self.update_thread = threading.Thread(target=self.update_processes)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def get_process_stats(self, pid):
        try:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.1)
            mem = process.memory_info().rss / 1024 / 1024  # Convert to MB
            return f"CPU: {cpu:.1f}% | MEM: {mem:.1f}MB"
        except:
            return "N/A"
    
    def update_processes(self):
        while self.running:
            try:
                # Update process list
                new_list = []
                for title, info in self.pm.processes.items():
                    stats = self.get_process_stats(info['pid']) if info['pid'] else "Stopped"
                    new_list.append({
                        'title': title,
                        'status': info['status'],
                        'pid': info['pid'] or '',
                        'stats': stats,
                        'autorun': '✓' if info['autorun'] else '✗'
                    })
                self.process_list = new_list
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Update error: {str(e)}")
                time.sleep(self.update_interval)
    
    def draw(self):
        try:
            print(self.term.clear())
            height = self.term.height
            width = self.term.width
            
            # Draw header
            header = "Python Process Manager"
            print(self.term.move(0, 0) + self.term.black_on_white(
                header.center(width)))
            print(self.term.move(1, 0) + "─" * width)
            
            # Draw column headers
            headers = ["Process Name", "Status", "System Stats", "Auto-Run"]
            header_format = "{:<30} {:<15} {:<25} {:<10}"
            print(self.term.move(2, 0) + self.term.bold(
                header_format.format(*headers)))
            print(self.term.move(3, 0) + "─" * width)
            
            # Draw processes
            for i, process in enumerate(self.process_list):
                if i >= height - 6:  # Leave space for headers and footer
                    break
                
                # Format process information
                status_color = self.term.green if process['status'] == 'running' else self.term.red
                line = header_format.format(
                    process['title'][:30],
                    status_color(process['status']),
                    process['stats'],
                    process['autorun']
                )
                
                y_pos = i + 4  # Start after headers
                if i == self.selected_index:
                    print(self.term.move(y_pos, 0) + self.term.black_on_white(line))
                else:
                    print(self.term.move(y_pos, 0) + line)
            
            # Draw footer
            footer = "↑/↓:Select | Enter:Start/Stop | r:Restart | q:Quit"
            print(self.term.move(height - 1, 0) + self.term.black_on_white(
                footer.center(width)))
            
            sys.stdout.flush()
        except Exception as e:
            print(f"Draw error: {str(e)}")
    
    def handle_input(self):
        with self.term.cbreak(), self.term.hidden_cursor():
            while self.running:
                try:
                    key = self.term.inkey(timeout=1)
                    if key:
                        if key.name == 'q':
                            self.running = False
                            break
                        elif key.name == 'up' or key.code == 65:
                            self.selected_index = max(0, self.selected_index - 1)
                        elif key.name == 'down' or key.code == 66:
                            self.selected_index = min(len(self.process_list) - 1, 
                                                   self.selected_index + 1)
                        elif key.name == 'enter':
                            if self.process_list:
                                title = self.process_list[self.selected_index]['title']
                                if self.pm.processes[title]['status'] == 'running':
                                    self.pm.stop(title)
                                else:
                                    self.pm.start(title)
                        elif key == 'r':
                            if self.process_list:
                                title = self.process_list[self.selected_index]['title']
                                self.pm.stop(title)
                                time.sleep(1)
                                self.pm.start(title)
                    self.draw()
                except Exception as e:
                    print(f"Input error: {str(e)}")
                    time.sleep(1)

def main():
    ui = TerminalUI()
    
    def signal_handler(signum, frame):
        ui.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        ui.handle_input()
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print(ui.term.clear())

if __name__ == "__main__":
    main()
