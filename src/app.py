"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['mergington_high']
activities_collection = db['activities']

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Activities are now stored in MongoDB

class SignupRequest(BaseModel):
    email: str


# Unregister endpoint (remove participant from activity)
@app.post("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, req: SignupRequest):
    """Remove a student from an activity"""
    email = req.email
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student not registered")
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    # Convert MongoDB cursor to dictionary with activity name as key
    activities_dict = {}
    for activity in activities_collection.find({}, {'_id': 0}):
        name = activity.pop('name')  # Remove name field from details
        activities_dict[name] = activity
    return activities_dict


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, req: SignupRequest):
    """Sign up a student for an activity"""
    email = req.email
    
    # Find the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if student is already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up")

    # Check if activity is full
    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    # Add student using MongoDB update
    result = activities_collection.update_one(
        {"name": activity_name},
        {"$push": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return {"message": f"Signed up {email} for {activity_name}"}
