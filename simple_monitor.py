#!/usr/bin/env python3
import time
import os
import sys
from process_manager import ProcessManager
import psutil

def clear_screen():
    os.system('clear')

def get_process_stats(pid):
    try:
        process = psutil.Process(pid)
        cpu = process.cpu_percent(interval=0.1)
        mem = process.memory_info().rss / 1024 / 1024  # Convert to MB
        return f"CPU: {cpu:.1f}% | MEM: {mem:.1f}MB"
    except:
        return "N/A"

def show_processes(pm, selected_index):
    clear_screen()
    print("\n=== Python Process Manager ===")
    print("\nProcesses:")
    print("-" * 80)
    print(f"{'Index':<6} {'Name':<25} {'Status':<10} {'System Stats':<25} {'Auto-Run':<8}")
    print("-" * 80)

    process_list = []
    for title, info in pm.processes.items():
        stats = get_process_stats(info['pid']) if info['pid'] else "Stopped"
        process_list.append({
            'title': title,
            'status': info['status'],
            'stats': stats,
            'autorun': '✓' if info['autorun'] else '✗'
        })

    for i, proc in enumerate(process_list):
        status_marker = '*' if i == selected_index else ' '
        status_color = '\033[92m' if proc['status'] == 'running' else '\033[91m'  # Green for running, red for stopped
        print(f"{status_marker} {i:<4} {proc['title']:<25} {status_color}{proc['status']:<10}\033[0m {proc['stats']:<25} {proc['autorun']:<8}")

    print("\n" + "-" * 80)
    print("Commands:")
    print("↑/↓ (8/2): Select process | Enter (5): Start/Stop | r: Restart | q: Quit")
    
    return process_list

def main():
    pm = ProcessManager()
    selected_index = 0
    last_key = None

    while True:
        process_list = show_processes(pm, selected_index)
        
        if not process_list:
            print("\nNo processes found. Add processes using: pypm save <name> <command>")
            time.sleep(2)
            continue

        try:
            key = input("\nEnter command: ").lower().strip()
            
            if key == 'q':
                clear_screen()
                break
            elif key in ['8', 'k']:  # Up
                selected_index = max(0, selected_index - 1)
            elif key in ['2', 'j']:  # Down
                selected_index = min(len(process_list) - 1, selected_index + 1)
            elif key == '5' or key == '':  # Enter/Start/Stop
                if process_list:
                    title = process_list[selected_index]['title']
                    if pm.processes[title]['status'] == 'running':
                        pm.stop(title)
                    else:
                        pm.start(title)
            elif key == 'r':  # Restart
                if process_list:
                    title = process_list[selected_index]['title']
                    pm.stop(title)
                    time.sleep(1)
                    pm.start(title)
            
            time.sleep(0.1)  # Small delay to prevent CPU overuse
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("\nMonitor stopped.")
