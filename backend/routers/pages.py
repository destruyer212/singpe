from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend import crud
from backend.config import ACCESS_PIN, TEMPLATES_DIR
from backend.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    config = crud.get_config(db)
    mesas = crud.listar_mesas(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "config": config, "mesas": mesas}
    )


@router.get("/mesa/{numero}")
def pagina_mesa(request: Request, numero: int, db: Session = Depends(get_db)):
    mesa = crud.get_or_create_mesa(db, numero)
    config = crud.get_config(db)
    return templates.TemplateResponse(
        "mesa.html", {"request": request, "mesa": mesa, "config": config}
    )


@router.get("/dj")
def pagina_dj(request: Request, db: Session = Depends(get_db)):
    config = crud.get_config(db)
    return templates.TemplateResponse("dj.html", {"request": request, "config": config, "access_pin": ACCESS_PIN})


@router.get("/tv")
def pagina_tv(request: Request, db: Session = Depends(get_db)):
    config = crud.get_config(db)
    return templates.TemplateResponse("tv.html", {"request": request, "config": config, "access_pin": ACCESS_PIN})


@router.get("/admin")
def pagina_admin(request: Request, db: Session = Depends(get_db)):
    config = crud.get_config(db)
    return templates.TemplateResponse("admin.html", {"request": request, "config": config, "access_pin": ACCESS_PIN})
