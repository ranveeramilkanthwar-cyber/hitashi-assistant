"""
Creates desktop shortcuts for Hitasha Control Center and Hitasha 3D Assistant.
"""

import os
import sys
import win32com.client

def create_shortcuts():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    icon_ico = os.path.join(project_dir, "assets", "hitasha_icon.ico")
    vbs_launcher = os.path.join(project_dir, "Start_Control_Center.vbs")

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop_dir = shell.SpecialFolders("Desktop")

    # 1. Hitasha Control Center (Start / Stop Manager)
    cc_shortcut_path = os.path.join(desktop_dir, "Hitasha Control Center.lnk")
    shortcut = shell.CreateShortCut(cc_shortcut_path)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = f'"{vbs_launcher}"'
    shortcut.WorkingDirectory = project_dir
    shortcut.Description = "Start, Stop, and Manage Hitasha 3D AI Assistant"
    if os.path.exists(icon_ico):
        shortcut.IconLocation = f"{icon_ico},0"
    shortcut.save()
    print(f"[Shortcut] Created: {cc_shortcut_path}")

    # 2. Hitasha 3D Assistant Direct Launcher
    companion_bat = os.path.join(project_dir, "Start_Hitasha.bat")
    asst_shortcut_path = os.path.join(desktop_dir, "Hitasha 3D Companion.lnk")
    shortcut2 = shell.CreateShortCut(asst_shortcut_path)
    shortcut2.TargetPath = companion_bat
    shortcut2.WorkingDirectory = project_dir
    shortcut2.Description = "Launch Hitasha 3D AI Desktop Companion"
    if os.path.exists(icon_ico):
        shortcut2.IconLocation = f"{icon_ico},0"
    shortcut2.save()
    print(f"[Shortcut] Created: {asst_shortcut_path}")

    return cc_shortcut_path, asst_shortcut_path

if __name__ == "__main__":
    create_shortcuts()
