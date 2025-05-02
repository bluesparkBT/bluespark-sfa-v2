import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )


app.include_router(AuthenticationRouter, prefix="/auth", tags=["auth"])
