import os
from fastapi import Request
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI
from routes.util import UtilRouter
from starlette.status import HTTP_400_BAD_REQUEST
from fastapi.middleware.cors import CORSMiddleware

from db import create_db_and_tables
from routes.serviceProvider import ServiceProvider
from routes.accounts import AccountRouter
from routes.address import AddressRouter
from routes.category import CategoryRouter
from routes.inheritance import InheritanceRouter
from routes.product import ProductRouter
from routes.role import RoleRouter
from routes.organizations import TenantRouter



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
@app.middleware("http")
async def extract_tenant(request: Request, call_next):
    path_parts = request.url.path.strip("/").split("/")
    # if parts:
    #     request.state.tenant = parts[0]
    if len(path_parts) > 0:
        request.state.tenant = path_parts[0]
    else:
        request.state.tenant = None
    response = await call_next(request)
    return response

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
    
app.include_router(AccountRouter, prefix="/{tenant}/account", tags=["account"])
app.include_router(AddressRouter, prefix="/{tenant}/address", tags=["address"])
app.include_router(CategoryRouter, prefix="/{tenant}/category", tags=["category"])
app.include_router(InheritanceRouter, prefix="/{tenant}/inheritance", tags = ["inheritance"])
app.include_router(TenantRouter, prefix="/{tenant}/organization", tags=["organization"])
app.include_router(ProductRouter, prefix="/{tenant}/product", tags=["product"])
app.include_router(RoleRouter, prefix="/{tenant}/role", tags=["role"])
app.include_router(UtilRouter, prefix="/{tenant}/utility", tags=["utility"])
app.include_router(ServiceProvider, tags=["service provider"])
#app.include_router(WarehouseRouter, prefix="/{tenant}/warehouse", tags=["warehouse"])
