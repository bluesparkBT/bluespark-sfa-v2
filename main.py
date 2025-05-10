import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI
from routes.Util import UtilRouter
from starlette.status import HTTP_400_BAD_REQUEST
from fastapi.middleware.cors import CORSMiddleware

from db import create_db_and_tables
from routes.accounts import AuthenticationRouter
from routes.organizations import TenantRouter
from routes.role import RoleRouter


load_dotenv()
ENV = os.getenv("ENV")

app = FastAPI(
    title="Bluespark SFA API",
    version="0.0.02 Beta",
    description="Bluespark API for sales force automation",
    middleware=[],
    swagger_ui_parameters={"docExpansion": "none", "tryItOutEnabled": True},
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": "Invalid input", "details": exc.errors()},
    )

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
app.include_router(AuthenticationRouter, prefix="/account", tags=["account"])
app.include_router(TenantRouter, prefix="/organization", tags=["organization"])
app.include_router(RoleRouter, prefix="/role", tags=["role"])
app.include_router(UtilRouter, prefix="/utility", tags=["Utility"])