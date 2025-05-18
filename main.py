#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import webview
from api import API

def main():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("Error: MONGO_URI not found in .env", file=sys.stderr)
        sys.exit(1)
    api = API()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    index_file = os.path.join(current_dir, "static", "index.html")
    webview.create_window("Time Tracker", index_file, js_api=api, width=800, height=600)
    webview.start(gui="qt")

if __name__ == "__main__":
    main()