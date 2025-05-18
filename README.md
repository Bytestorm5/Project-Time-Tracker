# Time Tracker

A desktop time tracking application built with pywebview and MongoDB.

## Features
- Define new projects (title, optional description, public flag)
- Clock in and clock out of projects
- View analytics of time spent per project

## Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the environment:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```powershell
     venv\\Scripts\\activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with your MongoDB connection string:
   ```text
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority
   ```

## Run
Ensure the virtual environment is activated and run:
```bash
python main.py
```