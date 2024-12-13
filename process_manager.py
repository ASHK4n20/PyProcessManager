import os
import sys
import yaml
import psutil
import subprocess
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from pathlib import Path

class ProcessManager:
    def __init__(self):
        self.home_dir = str(Path.home())
        self.config_dir = os.path.join(self.home_dir, '.pyprocessmanager')
        self.processes_file = os.path.join(self.config_dir, 'processes.yml')
        self.processes = {}
        self._init_config()
        self.console = Console()

    def _init_config(self):
        """Initialize configuration directory and files"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(self.processes_file):
            self._save_processes()
        else:
            self._load_processes()

    def _save_processes(self):
        """Save processes to YAML file"""
        with open(self.processes_file, 'w') as f:
            yaml.dump(self.processes, f)

    def _load_processes(self):
        """Load processes from YAML file"""
        if os.path.exists(self.processes_file):
            with open(self.processes_file, 'r') as f:
                self.processes = yaml.safe_load(f) or {}

    def save(self, title: str, command: str, cwd: str = None, autorun: bool = False):
        """Save a new command with title"""
        self.processes[title] = {
            'command': command,
            'cwd': cwd or os.getcwd(),
            'autorun': autorun,
            'pid': None,
            'status': 'stopped'
        }
        self._save_processes()
        self.console.print(f"[green]Saved command '{title}' successfully![/green]")

    def start(self, title: str):
        """Start a saved process"""
        if title not in self.processes:
            self.console.print(f"[red]No process found with title '{title}'[/red]")
            return

        process_info = self.processes[title]
        try:
            # First stop any existing process
            if process_info['pid']:
                self.stop(title)
                time.sleep(1)  # Give it time to stop

            # Prepare the command
            command = process_info['command']
            if command.startswith('python ') or command.startswith('python3 '):
                # Remove python/python3 prefix and use sys.executable
                command = command.replace('python3 ', '').replace('python ', '')
                command = f"{sys.executable} {command}"

            # Expand home directory if needed
            if '~' in command:
                command = command.replace('~', os.path.expanduser('~'))

            # Create log directory
            log_dir = os.path.join(self.config_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Setup log files
            stdout_log = os.path.join(log_dir, f"{title}.out")
            stderr_log = os.path.join(log_dir, f"{title}.err")
            
            # Create the command with proper output redirection
            full_command = f"nohup {command} > {stdout_log} 2> {stderr_log} & echo $!"

            # Execute the command
            process = subprocess.Popen(
                full_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=process_info['cwd'],
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Get the PID from the output
            pid_output = process.communicate()[0]
            if pid_output:
                pid = int(pid_output.strip())
                # Wait a bit to check if process is actually running
                time.sleep(0.5)
                try:
                    if psutil.Process(pid).is_running():
                        self.processes[title]['pid'] = pid
                        self.processes[title]['status'] = 'running'
                        self._save_processes()
                        self.console.print(f"[green]Started process '{title}' with PID {pid}[/green]")
                    else:
                        self.console.print(f"[red]Process '{title}' failed to start properly[/red]")
                except psutil.NoSuchProcess:
                    self.console.print(f"[red]Process '{title}' failed to start properly[/red]")
            else:
                self.console.print(f"[red]Failed to start process '{title}'[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting process '{title}': {str(e)}[/red]")

    def stop(self, title: str):
        """Stop a running process"""
        if title not in self.processes:
            self.console.print(f"[red]No process found with title '{title}'[/red]")
            return

        process_info = self.processes[title]
        if process_info['pid']:
            try:
                # Try to kill the process group
                try:
                    os.killpg(process_info['pid'], 9)
                except:
                    pass

                # Fallback: try to kill process and children individually
                try:
                    parent = psutil.Process(process_info['pid'])
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except:
                            pass
                    parent.kill()
                except:
                    pass
                
                self.processes[title]['pid'] = None
                self.processes[title]['status'] = 'stopped'
                self._save_processes()
                self.console.print(f"[green]Stopped process '{title}'[/green]")
            except Exception as e:
                self.console.print(f"[red]Error stopping process '{title}': {str(e)}[/red]")
                # Still mark as stopped since we tried our best
                self.processes[title]['pid'] = None
                self.processes[title]['status'] = 'stopped'
                self._save_processes()
        else:
            self.console.print(f"[yellow]Process '{title}' is not running[/yellow]")

    def is_process_running(self, pid):
        """Check if a process is actually running"""
        if not pid:
            return False
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except:
            return False

    def list(self):
        """List all saved processes and their status"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Title")
        table.add_column("Command")
        table.add_column("Status")
        table.add_column("PID")
        table.add_column("Auto-run")
        table.add_column("CPU %")
        table.add_column("MEM MB")

        for title, info in self.processes.items():
            # Verify process status
            if info['pid'] and not self.is_process_running(info['pid']):
                info['status'] = 'stopped'
                info['pid'] = None
                self._save_processes()

            # Get resource usage
            cpu_usage = "N/A"
            mem_usage = "N/A"
            if info['pid'] and info['status'] == 'running':
                try:
                    process = psutil.Process(info['pid'])
                    cpu_usage = f"{process.cpu_percent(interval=0.1):.1f}%"
                    mem_usage = f"{process.memory_info().rss / 1024 / 1024:.1f}"
                except:
                    pass

            status_color = "green" if info['status'] == 'running' else "red"
            table.add_row(
                title,
                info['command'],
                f"[{status_color}]{info['status']}[/{status_color}]",
                str(info['pid'] or ''),
                '✓' if info['autorun'] else '✗',
                cpu_usage,
                mem_usage
            )

        self.console.print(table)

    def setup_startup(self):
        """Setup autostart processes using systemd user services"""
        # Create systemd user directory if it doesn't exist
        systemd_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(systemd_dir, exist_ok=True)
        
        # Create logs directory
        log_dir = os.path.join(self.config_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create service files for each autorun process
        for title, info in self.processes.items():
            if info['autorun']:
                service_path = os.path.join(systemd_dir, f"pypm-{title}.service")
                command = info['command']
                if command.startswith('python ') or command.startswith('python3 '):
                    command = command.replace('python3 ', '').replace('python ', '')
                    command = f"{sys.executable} {command}"
                
                service_content = f"""[Unit]
Description=PyProcessManager - {title}
After=network.target

[Service]
Type=simple
WorkingDirectory={info['cwd']}
ExecStart={command}
Restart=always
StandardOutput=append:{os.path.join(self.config_dir, 'logs', f"{title}.out")}
StandardError=append:{os.path.join(self.config_dir, 'logs', f"{title}.err")}

[Install]
WantedBy=default.target
"""
                
                with open(service_path, 'w') as f:
                    f.write(service_content)
                
                try:
                    # Enable and start the service
                    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
                    subprocess.run(['systemctl', '--user', 'enable', f"pypm-{title}.service"], check=True)
                    subprocess.run(['systemctl', '--user', 'restart', f"pypm-{title}.service"], check=True)
                    self.console.print(f"[green]Setup autostart for '{title}'[/green]")
                except Exception as e:
                    self.console.print(f"[red]Error setting up autostart for '{title}': {str(e)}[/red]")

    def view_logs(self, title: str, follow: bool = False):
        """View logs for a process"""
        if title not in self.processes:
            self.console.print(f"[red]No process found with title '{title}'[/red]")
            return

        log_dir = os.path.join(self.config_dir, 'logs')
        stdout_log = os.path.join(log_dir, f"{title}.out")
        stderr_log = os.path.join(log_dir, f"{title}.err")

        if not os.path.exists(stdout_log) and not os.path.exists(stderr_log):
            self.console.print(f"[yellow]No logs found for '{title}'[/yellow]")
            return

        try:
            if follow:
                # Use tail -f to follow logs in real-time
                process = subprocess.Popen(['tail', '-f', stdout_log, stderr_log], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE,
                                        text=True)
                try:
                    while True:
                        line = process.stdout.readline()
                        if line:
                            self.console.print(line.strip())
                except KeyboardInterrupt:
                    process.terminate()
                    self.console.print("\n[yellow]Stopped following logs[/yellow]")
            else:
                # Show last 50 lines of logs
                if os.path.exists(stdout_log):
                    self.console.print("[bold]Standard Output:[/bold]")
                    output = subprocess.check_output(['tail', '-n', '50', stdout_log], text=True)
                    self.console.print(output)
                
                if os.path.exists(stderr_log):
                    self.console.print("\n[bold]Standard Error:[/bold]")
                    error = subprocess.check_output(['tail', '-n', '50', stderr_log], text=True)
                    self.console.print(error)
        except Exception as e:
            self.console.print(f"[red]Error viewing logs: {str(e)}[/red]")
