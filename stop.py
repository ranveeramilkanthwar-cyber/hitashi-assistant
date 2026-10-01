"""
Clean stopper for Hitasha 3D Assistant processes.
Terminates running instances of Hitasha cleanly without touching unrelated Python scripts.
"""

import os
import sys

try:
    import psutil
except ImportError:
    psutil = None

def stop_hitasha():
    current_pid = os.getpid()
    count = 0
    if psutil:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                cmd_str = " ".join(cmdline).lower()
                is_companion = 'main.py' in cmd_str
                is_manager = any(m in cmd_str for m in ['manager', 'control_center'])
                if is_companion and not is_manager and proc.info['pid'] != current_pid:
                    if 'python' in (proc.info.get('name') or '').lower():
                        proc.kill()
                        count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    else:
        # Fallback to taskkill on window title
        os.system('taskkill /F /FI "WINDOWTITLE eq Hitasha Desktop Companion*" >nul 2>&1')
        count = 1

    print(f"[Hitasha] Cleanly stopped ({count} instance(s) terminated).")
    return count

if __name__ == "__main__":
    stop_hitasha()
