import os
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict

import psutil
from pymongo import MongoClient

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import win32ts
except ImportError:  # allow module to compile on non-Windows systems
    win32gui = win32process = win32api = win32con = win32ts = None

IDLE_THRESHOLD = 300  # seconds
POLL_INTERVAL = 5

@dataclass
class Activity:
    app: str
    title: str
    details: Optional[str] = None

class ActivityMonitor:
    def __init__(self, mongo_uri: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_database("activity_tracker")
        self.col = self.db.get_collection("activities")
        self.current: Optional[Dict] = None

    def get_idle_seconds(self) -> int:
        if win32api is None:
            return 0
        info = win32api.GetLastInputInfo()
        millis = win32api.GetTickCount() - info
        return int(millis / 1000)

    def get_active_window_info(self) -> Optional[Activity]:
        if win32gui is None:
            return None
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        try:
            proc = psutil.Process(pid)
            app = proc.name().lower()
        except Exception:
            app = "unknown"
        title = win32gui.GetWindowText(hwnd)
        details = self.extract_details(app, title)
        return Activity(app=app, title=title, details=details)

    def extract_details(self, app: str, title: str) -> Optional[str]:
        app = app.lower()
        if "chrome" in app or "edge" in app:
            # window title usually "<page> - <profile> - Chrome"
            parts = title.split(" - ")
            if parts:
                return parts[0]
        if "discord" in app:
            # Discord titles "#channel - Server - Discord"
            parts = title.split(" - ")
            if len(parts) >= 2:
                return parts[1]
        if "code" in app:
            # VS Code titles "file (Workspace) - Visual Studio Code"
            parts = title.split(" - ")
            if parts:
                return parts[0]
        if "wsl" in app or "ubuntu" in app:
            return title
        return None

    def end_current(self, inactive: bool = False):
        if not self.current:
            return
        self.current["end_time"] = datetime.utcnow()
        self.current["inactive"] = inactive
        self.col.insert_one(self.current)
        self.current = None

    def start_new(self, activity: Activity):
        self.current = {
            "app": activity.app,
            "title": activity.title,
            "details": activity.details,
            "start_time": datetime.utcnow(),
        }

    def run(self):
        while True:
            idle = self.get_idle_seconds()
            if idle >= IDLE_THRESHOLD:
                self.end_current(inactive=True)
                time.sleep(POLL_INTERVAL)
                continue
            activity = self.get_active_window_info()
            if activity:
                if not self.current or self.current.get("title") != activity.title:
                    self.end_current()
                    self.start_new(activity)
            time.sleep(POLL_INTERVAL)

