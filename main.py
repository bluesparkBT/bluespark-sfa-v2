import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from db import create_db_and_tables
from routes.Tenants import TenantRouter
from routes.auth import AuthenticationRouter


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


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(AuthenticationRouter, prefix="/auth", tags=["auth"])
app.include_router(TenantRouter, prefix="/tenant", tags=["tenant"])
