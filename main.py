import os
from fastapi import FastAPI
# from routes.Util import UtilRouter
# from routes.policy import PolicyRouter

# from routes.category import CategoryRouter
# from routes.classification import ClassificationRouter
# from routes.deposit import DepositRouter
# from routes.organization import OrganizationRouter
# from routes.employee import EmployeeRouter

# from routes.warehouse import WarehouseRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from routes.address import AddressRouter
from routes.auth import AuthenticationRouter
# from utils.auth_util import auth_middleware

load_dotenv()
ENV = os.getenv("ENV")

app = FastAPI(
    title="Bluespark SFA API",
    version="0.0.01 Beta",
    description="Bluespark API for sales force automation",
    middleware=[],
    swagger_ui_parameters={"docExpansion": "none", "tryItOutEnabled": True},
)

# app.middleware("http")(auth_middleware)
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

app.include_router(AuthenticationRouter, prefix="/auth", tags=["Authentication"])
app.include_router(AddressRouter, prefix="/address", tags=["Addresses"])

# app.include_router(CategoryRouter, prefix="/category", tags=["Categories"])
# app.include_router(
#     ClassificationRouter, prefix="/classification", tags=["Classifications"]
# )

# app.include_router(DepositRouter, prefix="/deposit", tags=["Deposit"])
# app.include_router(EmployeeRouter, prefix="/employee", tags=["Employee"])
# app.include_router(
#     WarehouseStopRouter, prefix="/warehouse-stop", tags=["Warehouse Stop"]
# )
# app.include_router(WarehouseRouter, prefix="/warehouse", tags=["Warehouse"])
# app.include_router(UtilRouter, prefix="/utility", tags=["Utility"])

