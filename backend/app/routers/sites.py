from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SiteModel
from app.schemas import SiteOut
from app.services.scraping_core import SUPPORTED_SITE_SLUGS

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get(
    "",
    response_model=list[SiteOut],
    summary="Listar todos os sites de notícias suportados",
    response_description="Lista de sites de notícias com seus detalhes",
)
def list_sites(db: Session = Depends(get_db)) -> list[SiteOut]:
    """Retorna a lista completa de sites de notícias suportados pela plataforma.

    Este endpoint fornece informações sobre todos os sites de notícias que são
    monitorados pelo sistema, incluindo seus identificadores únicos (slugs),
    nomes e datas de criação.

    **Exemplos de uso:**

    - Listar todos os sites: `GET /sites`

    **Resposta:**

    Retorna um array com os seguintes dados para cada site:
    - `id`: Identificador único do site
    - `slug`: Identificador amigável (ex: veja, globo, cnn)
    - `name`: Nome completo do site
    - `created_at`: Data de criação do registro
    """
    sites = (
        db.query(SiteModel)
        .filter(SiteModel.slug.in_(SUPPORTED_SITE_SLUGS))
        .order_by(SiteModel.name)
        .all()
    )
    return [SiteOut.model_validate(site) for site in sites]
