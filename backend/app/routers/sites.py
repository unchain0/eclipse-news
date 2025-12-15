from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SiteModel
from app.schemas import SiteOut
from app.services.scraping_core import SUPPORTED_SITE_SLUGS

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteOut], summary="List all supported news sites")
def list_sites(db: Session = Depends(get_db)) -> list[SiteOut]:
    """
    List all supported news sites.

    Args:
        db: Database session

    Returns:
        List of supported news sites with their details
    """
    sites = (
        db.query(SiteModel)
        .filter(SiteModel.slug.in_(SUPPORTED_SITE_SLUGS))
        .order_by(SiteModel.name)
        .all()
    )
    return [SiteOut.model_validate(site) for site in sites]
