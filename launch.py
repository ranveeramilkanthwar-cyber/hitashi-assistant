"""
Launcher for Hitasha 3D Assistant directly onto Windows interactive user desktop (WinSta0\\default).
"""

import os
import sys
import subprocess
import time

def launch():
    # 1. First ensure any previous instance is stopped
    try:
        from stop import stop_hitasha
        stop_hitasha()
    except Exception:
        pass

    workdir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(workdir, "Start_Hitasha.bat")
    task_tr = f'C:\\Windows\\System32\\cmd.exe /c ""{bat_path}""'

    print("[Hitasha] Launching on user interactive desktop...")
    # Use schtasks with /it (interactive token)
    res_create = subprocess.run([
        'schtasks', '/create',
        '/tn', 'HitashaLauncher',
        '/tr', task_tr,
        '/sc', 'ONCE',
        '/st', '23:59',
        '/f',
        '/it'
    ], capture_output=True, text=True)

    res_run = subprocess.run([
        'schtasks', '/run',
        '/tn', 'HitashaLauncher'
    ], capture_output=True, text=True)

    time.sleep(2)
    # Check if pythonw.exe is running
    import psutil
    count = 0
    pids = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = (p.info.get('name') or '').lower()
            cmdline = ' '.join(p.info.get('cmdline') or [])
            if 'pythonw' in name and 'main.py' in cmdline:
                count += 1
                pids.append(p.info['pid'])
        except Exception:
            pass

    if count > 0:
        print(f"[Hitasha] SUCCESS: Hitasha is now running on your desktop ({count} active process(es), PIDs: {pids})!")
        return True, pids
    else:
        # Fallback to direct process spawn
        pythonw_path = os.path.join(workdir, ".venv", "Scripts", "pythonw.exe")
        main_py = os.path.join(workdir, "main.py")
        proc = subprocess.Popen([pythonw_path, main_py], cwd=workdir)
        print(f"[Hitasha] Launched via direct subprocess on desktop (PID: {proc.pid})!")
        return True, [proc.pid]

if __name__ == "__main__":
    launch()

