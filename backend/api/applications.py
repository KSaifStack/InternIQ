from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models import models, schemas, database

router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.get("/user/{user_id}", response_model=List[schemas.Application])
def get_user_applications(user_id: int, db: Session = Depends(database.get_db)):
    apps = db.query(models.Application).filter(models.Application.user_id == user_id).all()
    return apps

@router.post("/user/{user_id}", response_model=schemas.Application)
def create_application(user_id: int, app_in: schemas.ApplicationCreate, db: Session = Depends(database.get_db)):
    # Check if job exists
    job = db.query(models.JobListing).filter(models.JobListing.id == app_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db_app = db.query(models.Application).filter(
        models.Application.user_id == user_id, 
        models.Application.job_id == app_in.job_id
    ).first()
    
    if db_app:
         raise HTTPException(status_code=400, detail="Application already tracked")

    new_app = models.Application(user_id=user_id, **app_in.model_dump())
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@router.put("/{app_id}", response_model=schemas.Application)
def update_application(app_id: int, app_update: schemas.ApplicationUpdate, db: Session = Depends(database.get_db)):
    db_app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app_update.status:
        db_app.status = app_update.status
    if app_update.notes:
        db_app.notes = app_update.notes
        
    db.commit()
    db.refresh(db_app)
    return db_app
