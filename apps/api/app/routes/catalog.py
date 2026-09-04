from fastapi import APIRouter

from apps.api.app.catalog.catalog_service import get_catalog


router = APIRouter(
    prefix="/api/catalog",
    tags=["Catalog"]
)


@router.get("")
def catalog():
    return get_catalog()
