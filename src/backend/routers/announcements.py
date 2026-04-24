"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson.objectid import ObjectId

from ..database import announcements_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (not expired yet)"""
    today = datetime.now().date().isoformat()
    
    # Query for announcements that are either not started yet or currently active
    # and haven't expired yet
    announcements = list(announcements_collection.find(
        {
            "$or": [
                {"start_date": None},  # No start date means it's active immediately
                {"start_date": {"$lte": today}}  # Or it has started
            ],
            "expiration_date": {"$gte": today}  # And hasn't expired
        }
    ).sort("created_date", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (admin only)"""
    from ..database import teachers_collection
    
    # Check if user is authenticated and is admin
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    announcements = list(announcements_collection.find().sort("created_date", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.post("")
def create_announcement(
    username: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement (auth required)"""
    from ..database import teachers_collection
    
    # Check if user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate dates
    try:
        exp_date = datetime.fromisoformat(expiration_date).date()
        start_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date).date()
            if start_dt > exp_date:
                raise ValueError("Start date cannot be after expiration date")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_date": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    username: str,
    announcement_id: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an announcement (auth required)"""
    from ..database import teachers_collection
    
    # Check if user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate dates
    try:
        exp_date = datetime.fromisoformat(expiration_date).date()
        start_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date).date()
            if start_dt > exp_date:
                raise ValueError("Start date cannot be after expiration date")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    # Find and update the announcement
    update_data = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_by": username,
        "updated_date": datetime.now().isoformat()
    }
    
    result = announcements_collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    result["_id"] = str(result["_id"])
    return result


@router.delete("/{announcement_id}")
def delete_announcement(username: str, announcement_id: str) -> Dict[str, str]:
    """Delete an announcement (auth required)"""
    from ..database import teachers_collection
    
    # Check if user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
