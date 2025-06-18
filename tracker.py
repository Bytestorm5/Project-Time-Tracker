import os
from dotenv import load_dotenv

from activity_monitor import ActivityMonitor
from classifier import ActivityClassifier


def main():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise SystemExit("MONGO_URI not set")

    monitor = ActivityMonitor(mongo_uri)
    classifier = ActivityClassifier(monitor.col)
    classifier.train()
    monitor.run()


if __name__ == "__main__":
    main()

