from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SiteModel
from app.schemas import SiteOut


router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteOut])
def list_sites(db: Session = Depends(get_db)) -> list[SiteOut]:
    sites = db.query(SiteModel).order_by(SiteModel.name).all()
    return [SiteOut.model_validate(site) for site in sites]
