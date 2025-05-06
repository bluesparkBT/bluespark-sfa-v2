import os

from sqlmodel import create_engine, Session

# Docker get the environment variables
# SECRET_KEY = os.environ["SECRET_KEY"]
# POSTGRES = os.environ["POSTGRES"]

# Virtual Environment
from dotenv import load_dotenv
from sqlmodel import SQLModel

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
POSTGRES = os.getenv("POSTGRES")


if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

if not POSTGRES:
    raise ValueError("POSTGRES environment variable is required")

engine = create_engine(POSTGRES)


def get_session():
    with Session(engine) as session:
        yield session
        
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)