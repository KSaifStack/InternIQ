from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..models import models, schemas, database

router = APIRouter(prefix="/api/companies", tags=["companies"])

@router.get("/", response_model=list)
def read_companies(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Company)
    if search:
        query = query.filter(models.Company.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/{company_id}", response_model=schemas.Company)
def read_company(company_id: int, db: Session = Depends(database.get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/{company_id}", response_model=schemas.Company)
def update_company(
    company_id: int, 
    company_update: schemas.CompanyBase,
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
        
    db.commit()
    db.refresh(company)
    return company
