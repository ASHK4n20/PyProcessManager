# PyProcessManager

A Python-based process manager similar to PM2, with both CLI and GUI interfaces.

## Features

- Process Management
  - Start, stop, and restart processes
  - Monitor CPU and memory usage
  - Auto-start processes on system boot
  - Detailed logging for each process

- User Interface
  - Modern GUI with process list, log viewer, and process manager
  - Command-line interface for quick actions
  - Real-time process monitoring
  - Easy-to-use process configuration

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/PyProcessManager.git
cd PyProcessManager

# Install the package
pip install -e .
```

## Usage

### GUI Interface

Launch the GUI application:
```bash
pypm gui
```

The GUI has three tabs:
1. **Processes**: View and manage all processes
2. **Logs**: View real-time logs for any process
3. **Add Process**: Add new processes to manage

### Command Line Interface

```bash
# Add a new process
pypm save myprocess "python script.py" --autorun

# Start a process
pypm start myprocess

# Stop a process
pypm stop myprocess

# Restart a process
pypm restart myprocess

# View process logs
pypm logs myprocess

# Follow logs in real-time
pypm logs -f myprocess

# Setup autostart for processes
pypm setup-startup
```

## Configuration

Processes are stored in `~/.pyprocessmanager/processes.yml`
Logs are stored in `~/.pyprocessmanager/logs/`

## Dependencies

- psutil: Process and system utilities
- tkinter: GUI framework
- PyYAML: Configuration file handling

## License

MIT License
