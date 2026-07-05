from fastapi import APIRouter

from app.ontology.catalog import CATALOG
from app.ontology.models import OntologyCatalog

router = APIRouter(prefix="/api/ontology", tags=["ontology"])


@router.get("", response_model=OntologyCatalog)
def get_ontology() -> OntologyCatalog:
    return CATALOG

