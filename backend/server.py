from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt, JWTError
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Supabase JWT configuration
SUPABASE_JWT_SECRET = os.environ['SUPABASE_JWT_SECRET']
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="CORE - Conscious Observation Reconstruction Engine API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supabase_uid: str
    email: str
    full_name: Optional[str] = None
    therapy_preferences: Optional[List[str]] = []
    vr_settings: Optional[dict] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    full_name: Optional[str] = None
    therapy_preferences: Optional[List[str]] = []
    vr_settings: Optional[dict] = {}

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    therapy_preferences: Optional[List[str]] = None
    vr_settings: Optional[dict] = None

# Authentication dependency
async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token from Supabase and return user information
    """
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": 'Bearer realm="auth_required"'},
        )
    
    try:
        payload = jwt.decode(
            cred.credentials,
            SUPABASE_JWT_SECRET,
            audience="authenticated",
            algorithms=["HS256"],
        )
        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "exp": payload.get("exp")
        }
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": 'Bearer realm="auth_required"'},
        )

# Authentication routes
@api_router.get("/auth/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "user_id": user["sub"],
        "email": user["email"],
        "role": user["role"]
    }

@api_router.get("/auth/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    """Example protected route"""
    return {
        "message": "Access granted to CORE platform",
        "user_email": user["email"],
        "platform": "CORE - Conscious Observation Reconstruction Engine"
    }

# User profile routes
@api_router.post("/profile", response_model=UserProfile)
async def create_user_profile(
    profile_data: UserProfileCreate,
    user: dict = Depends(get_current_user)
):
    """Create or update user profile in MongoDB"""
    # Check if profile already exists
    existing_profile = await db.user_profiles.find_one({"supabase_uid": user["sub"]})
    
    if existing_profile:
        # Update existing profile
        update_data = profile_data.dict(exclude_none=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await db.user_profiles.update_one(
            {"supabase_uid": user["sub"]},
            {"$set": update_data}
        )
        
        # Return updated profile
        updated_profile = await db.user_profiles.find_one({"supabase_uid": user["sub"]})
        return UserProfile(**updated_profile)
    else:
        # Create new profile
        profile = UserProfile(
            supabase_uid=user["sub"],
            email=user["email"],
            **profile_data.dict(exclude_none=True)
        )
        
        await db.user_profiles.insert_one(profile.dict())
        return profile

@api_router.get("/profile", response_model=UserProfile)
async def get_user_profile(user: dict = Depends(get_current_user)):
    """Get user profile from MongoDB"""
    profile = await db.user_profiles.find_one({"supabase_uid": user["sub"]})
    
    if not profile:
        # Create basic profile if doesn't exist
        basic_profile = UserProfile(
            supabase_uid=user["sub"],
            email=user["email"]
        )
        await db.user_profiles.insert_one(basic_profile.dict())
        return basic_profile
    
    return UserProfile(**profile)

@api_router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    user: dict = Depends(get_current_user)
):
    """Update user profile in MongoDB"""
    update_data = profile_update.dict(exclude_none=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.user_profiles.update_one(
        {"supabase_uid": user["sub"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    updated_profile = await db.user_profiles.find_one({"supabase_uid": user["sub"]})
    return UserProfile(**updated_profile)

# VR Session routes (example of platform-specific functionality)
@api_router.get("/vr/sessions")
async def get_vr_sessions(user: dict = Depends(get_current_user)):
    """Get VR therapy sessions for the current user"""
    # This would typically fetch actual VR session data
    return {
        "user_id": user["sub"],
        "sessions": [
            {
                "id": str(uuid.uuid4()),
                "title": "Memory Reconstruction Session #1",
                "date": datetime.utcnow(),
                "duration": 30,
                "type": "therapeutic_memory_replay"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Cognitive Behavioral Therapy Session",
                "date": datetime.utcnow(),
                "duration": 45,
                "type": "cbt_immersion"
            }
        ]
    }

# Legacy routes (keeping them for backward compatibility)
@api_router.get("/")
async def root():
    return {"message": "CORE - Conscious Observation Reconstruction Engine API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("CORE API starting up...")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("CORE API shutting down...")
    client.close()