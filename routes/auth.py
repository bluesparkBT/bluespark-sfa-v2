from fastapi import APIRouter, HTTPException, Body, status, Depends
from sqlmodel import select, Session
from db import get_session
from models.auth import User
from utils.auth_util import verify_password, create_access_token, get_password_hash

AuthenticationRouter =ar= APIRouter()

@ar.post("/login/")
def login(
    session: Session = Depends(get_session),
    username: str = Body(...),
    password: str = Body(...)
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.passhash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token}




@ar.post("/register/")
def register(
    session: Session = Depends(get_session),
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...)
):
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create user
    new_user = User(username=username, email=email, passhash=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Optionally return access token
    token = create_access_token(data={"sub": new_user.username})
    return {
        "message": "User registered successfully",
        "access_token": token
    }
