# Implementation Plan for Automatic Activity Detection

This repository aims to build a local desktop application that automatically detects the user's activity on Windows. The existing manual tracker is deprecated.

## Target Platforms
- **Windows** first
- Other OSes can be added later using the same architecture

## Programming Language
Use **Python** for its Windows API support and ease of maintenance.

## Key Features
1. **Automatic Activity Recognition**
   - Detect active browser tab, Discord server, VS Code workspace, or WSL directory
2. **Inactivity Detection**
   - Monitor lock/unlock events and idle time using `GetLastInputInfo`
3. **Local Data Storage**
   - Store events in **MongoDB** via the `MONGO_URI` environment variable
4. **Clustering**
   - Periodically cluster activity details with K-Means to infer categories
5. **Simple UI**
   - A small local dashboard (e.g., `pywebview`) may be added later

## Core Libraries
- `pywin32` for window titles and session events
- `psutil` for process inspection
- `pywinauto` for reading UI elements like browser URLs
- `pymongo` for MongoDB storage
- `scikit-learn` for clustering

## Development Steps
1. Module for active window detection
2. Handlers for Browser, Discord, VS Code, and WSL
3. Idle detection
4. MongoDB logging functions
5. Clustering module
6. Optional UI to view logs

All detection happens locally; no data leaves the machine unless stored in the user's own database.
