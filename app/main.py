from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, root_path=settings.api_root_path)
app.include_router(router)
