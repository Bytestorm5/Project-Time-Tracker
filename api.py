import os
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, ASCENDING

class API:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client.get_database("time_tracker")
        self.projects = self.db.get_collection("projects")
        self.time_entries = self.db.get_collection("time_entries")
        self.milestones = self.db.get_collection("milestones")

    def add_project(self, title, description="", public=False):
        if not title:
            return {"error": "Title is required"}
        doc = {
            "title": title,
            "description": description,
            "public": bool(public),
            "created_at": datetime.utcnow(),
        }
        result = self.projects.insert_one(doc)
        return {"inserted_id": str(result.inserted_id)}

    def get_projects(self):
        docs = list(self.projects.find().sort("created_at", ASCENDING))
        projects = []
        for doc in docs:
            projects.append({
                "_id": str(doc["_id"]),
                "title": doc.get("title", ""),
                "description": doc.get("description", ""),
                "public": doc.get("public", False),
                "created_at": doc.get("created_at").isoformat(),
            })
        return projects

    def clock_in(self, project_id):
        try:
            pid = ObjectId(project_id)
        except Exception:
            return {"error": "Invalid project ID"}
        existing = self.time_entries.find_one({
            "project_id": pid,
            "end_time": None
        })
        if existing:
            return {"error": "Already clocked in to this project"}
        doc = {
            "project_id": pid,
            "start_time": datetime.utcnow(),
            "end_time": None
        }
        result = self.time_entries.insert_one(doc)
        return {"inserted_id": str(result.inserted_id)}

    def clock_out(self, project_id):
        try:
            pid = ObjectId(project_id)
        except Exception:
            return {"error": "Invalid project ID"}
        entry = self.time_entries.find_one({
            "project_id": pid,
            "end_time": None
        })
        if not entry:
            return {"error": "No active entry for this project"}
        now = datetime.utcnow()
        self.time_entries.update_one(
            {"_id": entry["_id"]},
            {"$set": {"end_time": now}}
        )
        return {"status": "ok"}

    def get_analytics(self):
        # Sum total duration per project for completed entries
        pipeline = [
            {"$match": {"end_time": {"$ne": None}}},
            {
                "$project": {
                    "project_id": 1,
                    "duration_ms": {"$subtract": ["$end_time", "$start_time"]}
                }
            },
            {
                "$group": {
                    "_id": "$project_id",
                    "total_duration_ms": {"$sum": "$duration_ms"}
                }
            },
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "project"
                }
            },
            {"$unwind": "$project"},
            {
                "$project": {
                    "_id": 0,
                    "project_id": {"$toString": "$_id"},
                    "title": "$project.title",
                    "total_hours": {"$divide": ["$total_duration_ms", 1000 * 60 * 60]}
                }
            }
        ]
        results = list(self.time_entries.aggregate(pipeline))
        return results
    def get_daily_analytics(self):
        """
        Returns total hours per project per day.
        """
        pipeline = [
            {"$match": {"end_time": {"$ne": None}}},
            {"$project": {
                "project_id": 1,
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$start_time"}},
                "duration_ms": {"$subtract": ["$end_time", "$start_time"]}
            }},
            {"$group": {
                "_id": {"project_id": "$project_id", "day": "$day"},
                "total_duration_ms": {"$sum": "$duration_ms"}
            }},
            {"$lookup": {
                "from": "projects",
                "localField": "_id.project_id",
                "foreignField": "_id",
                "as": "project"
            }},
            {"$unwind": "$project"},
            {"$project": {
                "_id": 0,
                "project_id": {"$toString": "$_id.project_id"},
                "day": "$_id.day",
                "title": "$project.title",
                "total_hours": {"$divide": ["$total_duration_ms", 1000 * 60 * 60]}
            }}
        ]
        results = list(self.time_entries.aggregate(pipeline))
        return results
    
    def get_active_entry(self):
        entry = self.time_entries.find_one({"end_time": None})
        if not entry:
            return None
        # Return start_time in ISO 8601 UTC (with Z) to ensure correct JS parsing
        iso = entry["start_time"].isoformat()
        # If naive datetime, append 'Z' to indicate UTC
        if not iso.endswith('Z') and '+' not in iso and '-' not in iso[10:]:
            iso = iso + 'Z'
        return {
            "_id": str(entry["_id"]),
            "project_id": str(entry["project_id"]),
            "start_time": iso
        }

    def edit_project(self, project_id, title, description="", public=False):
        try:
            pid = ObjectId(project_id)
        except Exception:
            return {"error": "Invalid project ID"}
        if not title:
            return {"error": "Title is required"}
        result = self.projects.update_one(
            {"_id": pid},
            {"$set": {
                "title": title,
                "description": description,
                "public": bool(public)
            }}
        )
        if result.matched_count == 0:
            return {"error": "Project not found"}
        return {"status": "ok"}

    def delete_project(self, project_id):
        try:
            pid = ObjectId(project_id)
        except Exception:
            return {"error": "Invalid project ID"}
        result = self.projects.delete_one({"_id": pid})
        if result.deleted_count == 0:
            return {"error": "Project not found"}
        # Remove associated time entries
        self.time_entries.delete_many({"project_id": pid})
        return {"status": "ok"}
    
    # Milestone CRUD
    def add_milestone(self, project_id, title, description="", public=False, significance="Incremental"):
        try:
            pid = ObjectId(project_id)
        except Exception:
            return {"error": "Invalid project ID"}
        if not title:
            return {"error": "Title is required"}
        if significance not in ["Landmark", "Major", "Incremental"]:
            return {"error": "Invalid significance"}
        doc = {
            "project_id": pid,
            "title": title,
            "description": description,
            "public": bool(public),
            "significance": significance,
            "timestamp": datetime.utcnow()
        }
        result = self.milestones.insert_one(doc)
        return {"inserted_id": str(result.inserted_id)}

    def get_milestones(self, project_id):
        try:
            pid = ObjectId(project_id)
        except Exception:
            return {"error": "Invalid project ID"}
        docs = list(self.milestones.find({"project_id": pid}).sort("timestamp", ASCENDING))
        milestones = []
        for doc in docs:
            ts = doc.get("timestamp")
            milestones.append({
                "_id": str(doc["_id"]),
                "project_id": str(doc["project_id"]),
                "title": doc.get("title", ""),
                "description": doc.get("description", ""),
                "public": doc.get("public", False),
                "significance": doc.get("significance", "Incremental"),
                "timestamp": ts.isoformat() + 'Z' if ts and isinstance(ts, datetime) else None
            })
        return milestones

    def edit_milestone(self, milestone_id, title, description="", public=False, significance="Incremental"):
        try:
            mid = ObjectId(milestone_id)
        except Exception:
            return {"error": "Invalid milestone ID"}
        if not title:
            return {"error": "Title is required"}
        if significance not in ["Landmark", "Major", "Incremental"]:
            return {"error": "Invalid significance"}
        result = self.milestones.update_one(
            {"_id": mid},
            {"$set": {"title": title, "description": description, "public": bool(public), "significance": significance}}
        )
        if result.matched_count == 0:
            return {"error": "Milestone not found"}
        return {"status": "ok"}

    def delete_milestone(self, milestone_id):
        try:
            mid = ObjectId(milestone_id)
        except Exception:
            return {"error": "Invalid milestone ID"}
        result = self.milestones.delete_one({"_id": mid})
        if result.deleted_count == 0:
            return {"error": "Milestone not found"}
        return {"status": "ok"}