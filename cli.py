#!/usr/bin/env python3
import click
from process_manager import ProcessManager
from simple_monitor import main as monitor_main

pm = ProcessManager()

@click.group()
def cli():
    """Python Process Manager - A simple process manager for your commands"""
    pass

@cli.command()
@click.argument('title')
@click.argument('command')
@click.option('--cwd', help='Working directory for the command')
@click.option('--autorun', is_flag=True, help='Auto-run on system startup')
def save(title, command, cwd=None, autorun=False):
    """Save a command with a title"""
    pm.save(title, command, cwd, autorun)

@cli.command()
@click.argument('title')
def start(title):
    """Start a saved process"""
    pm.start(title)

@cli.command()
@click.argument('title')
def stop(title):
    """Stop a running process"""
    pm.stop(title)

@cli.command()
def list():
    """List all saved processes"""
    pm.list()

@cli.command()
def gui_list():
    """List processes with GUI"""
    from gui_list import main
    main()

@cli.command()
@click.argument('title')
@click.option('--follow', '-f', is_flag=True, help='Follow log output in real-time')
def logs(title, follow=False):
    """View logs for a process"""
    pm.view_logs(title, follow)

@cli.command()
def monitor():
    """Monitor all processes with terminal UI"""
    monitor_main()

@cli.command()
def setup_startup():
    """Setup autostart for processes marked with autorun"""
    pm.setup_startup()

@cli.command()
def gui():
    """Open the terminal UI application"""
    from tui import main
    main()

if __name__ == '__main__':
    cli()
