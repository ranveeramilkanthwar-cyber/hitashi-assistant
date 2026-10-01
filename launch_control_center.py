"""
Launcher for Hitasha Control Center directly onto Windows interactive user desktop (WinSta0\\default).
"""

import os
import sys
import subprocess
import time

def launch_control_center():
    workdir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(workdir, "Hitasha_Control_Center.bat")
    task_tr = f'C:\\Windows\\System32\\cmd.exe /c ""{bat_path}""'

    print("[Control Center] Launching on user interactive desktop...")
    # Use schtasks with /it (interactive token)
    res_create = subprocess.run([
        'schtasks', '/create',
        '/tn', 'HitashaControlCenter',
        '/tr', task_tr,
        '/sc', 'ONCE',
        '/st', '23:59',
        '/f',
        '/it'
    ], capture_output=True, text=True)

    res_run = subprocess.run([
        'schtasks', '/run',
        '/tn', 'HitashaControlCenter'
    ], capture_output=True, text=True)

    time.sleep(2)

    import psutil
    count = 0
    pids = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = (p.info.get('name') or '').lower()
            cmdline = ' '.join(p.info.get('cmdline') or [])
            if 'pythonw' in name and 'control_center' in cmdline:
                count += 1
                pids.append(p.info['pid'])
        except Exception:
            pass

    if count > 0:
        print(f"[Control Center] SUCCESS: Hitasha Control Center is running on your desktop (PIDs: {pids})!")
        return True, pids
    else:
        # Fallback to direct process spawn
        pythonw_path = os.path.join(workdir, ".venv", "Scripts", "pythonw.exe")
        cc_py = os.path.join(workdir, "control_center.py")
        proc = subprocess.Popen([pythonw_path, cc_py], cwd=workdir)
        print(f"[Control Center] Launched via direct subprocess on desktop (PID: {proc.pid})!")
        return True, [proc.pid]

if __name__ == "__main__":
    launch_control_center()
