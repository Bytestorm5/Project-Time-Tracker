# Activity Tracker

A local Windows application that automatically detects what you're doing and logs activities to MongoDB.

## Features
- Detect active application and context (browser tabs, Discord server, VS Code folder, WSL path).
- Detect inactivity based on idle time.
- Store all activity events in MongoDB using the `MONGO_URI` environment variable.
- Basic clustering of activities using K-Means to infer categories.

## Setup
1. Create and activate a virtual environment
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Add a `.env` file with your MongoDB connection string
   ```text
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority
   ```

## Run
```bash
python tracker.py
```
