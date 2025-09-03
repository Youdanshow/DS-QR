from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re
import aiohttp
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Founder promo code
FOUNDER_PROMO_CODE = "QR-8K9M7-F3X2L"

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# User Models
class User(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    isPremium: bool = False
    isFounder: bool = False
    qrCodeCount: int = 0
    subscriptionExpiresAt: Optional[datetime] = None

class UserLimits(BaseModel):
    used: int
    max: Union[int, str]
    isPremium: bool
    isFounder: bool = False

# QR Code Models
class QRCodeCreate(BaseModel):
    url: str
    size: str = "150x150"

class QRCode(BaseModel):
    id: str
    url: str
    qrCodeUrl: str
    size: str
    downloaded: bool = False
    createdAt: datetime

# Response Models
class QRResponse(BaseModel):
    qrCode: QRCode
    limits: UserLimits

class QRHistoryResponse(BaseModel):
    qrCodes: List[QRCode]
    limits: UserLimits

# Subscription Models
class SubscriptionUpgrade(BaseModel):
    planType: str = "monthly"

class PromoCodeRedeem(BaseModel):
    promoCode: str

class Subscription(BaseModel):
    id: str
    planType: str
    status: str
    expiresAt: datetime

# Utility Functions
def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_size(size: str) -> bool:
    pattern = r'^\d{2,4}x\d{2,4}$'
    if not re.match(pattern, size):
        return False
    
    width, height = map(int, size.split('x'))
    return 50 <= width <= 1000 and 50 <= height <= 1000

async def get_user_from_session(session_token: str) -> Optional[dict]:
    """Get user from session token stored in database"""
    session = await db.sessions.find_one({
        "session_token": session_token,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not session:
        return None
    
    # Get user data
    user = await db.users.find_one({"_id": session["user_id"]})
    return user

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from session cookie or Authorization header"""
    session_token = None
    
    # Try to get session token from cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token and credentials:
        session_token = credentials.credentials
    
    if not session_token:
        return None
    
    return await get_user_from_session(session_token)

async def get_user_limits(user: Optional[dict], request: Request) -> UserLimits:
    if user:
        # Check if user is founder (permanent premium)
        is_founder = user.get("isFounder", False)
        
        # Check if user has active premium subscription (if not founder)
        subscription = None
        if not is_founder:
            subscription = await db.subscriptions.find_one({
                "userId": user["_id"],
                "status": "active",
                "expiresAt": {"$gt": datetime.utcnow()}
            })
        
        is_premium = is_founder or subscription is not None
        
        return UserLimits(
            used=user.get("qrCodeCount", 0),
            max="unlimited" if is_premium else 5,
            isPremium=is_premium,
            isFounder=is_founder
        )
    else:
        # Guest user - count by IP
        guest_ip = request.client.host
        guest_count = await db.qr_codes.count_documents({"guestIp": guest_ip})
        
        return UserLimits(
            used=guest_count,
            max=3,
            isPremium=False,
            isFounder=False
        )

async def check_generation_limit(user: Optional[dict], request: Request) -> bool:
    limits = await get_user_limits(user, request)
    
    if limits.max == "unlimited":
        return True
    
    return limits.used < limits.max

# Authentication Routes
@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Create session from Emergent Auth session_id"""
    try:
        body = await request.json()
        session_id = body.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Call Emergent Auth API to get user data
        async with aiohttp.ClientSession() as session:
            headers = {"X-Session-ID": session_id}
            async with session.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers=headers
            ) as auth_response:
                if auth_response.status != 200:
                    raise HTTPException(status_code=401, detail="Invalid session")
                
                auth_data = await auth_response.json()
        
        # Extract user data
        user_id = auth_data["id"]
        email = auth_data["email"]
        name = auth_data["name"]
        picture = auth_data.get("picture", "")
        session_token = auth_data["session_token"]
        
        # Check if user already exists
        existing_user = await db.users.find_one({"_id": user_id})
        
        if not existing_user:
            # Create new user
            user_doc = {
                "_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "isPremium": False,
                "isFounder": False,
                "qrCodeCount": 0,
                "subscriptionExpiresAt": None,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            await db.users.insert_one(user_doc)
        
        # Create/update session
        session_doc = {
            "session_token": session_token,
            "user_id": user_id,
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "created_at": datetime.utcnow()
        }
        
        await db.sessions.replace_one(
            {"user_id": user_id},
            session_doc,
            upsert=True
        )
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        # Get user data for response
        user = await db.users.find_one({"_id": user_id})
        user_obj = User(
            id=user["_id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture", ""),
            isPremium=user.get("isPremium", False),
            isFounder=user.get("isFounder", False),
            qrCodeCount=user.get("qrCodeCount", 0),
            subscriptionExpiresAt=user.get("subscriptionExpiresAt")
        )
        
        limits = await get_user_limits(user, request)
        
        return {"user": user_obj, "limits": limits}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@api_router.get("/auth/me")
async def get_current_user_info(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_obj = User(
        id=user["_id"],
        email=user["email"],
        name=user["name"],
        picture=user.get("picture", ""),
        isPremium=user.get("isPremium", False),
        isFounder=user.get("isFounder", False),
        qrCodeCount=user.get("qrCodeCount", 0),
        subscriptionExpiresAt=user.get("subscriptionExpiresAt")
    )
    
    limits = await get_user_limits(user, request)
    
    return {"user": user_obj, "limits": limits}

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, user: dict = Depends(get_current_user)):
    if user:
        # Delete session from database
        await db.sessions.delete_many({"user_id": user["_id"]})
    
    # Clear session cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"success": True}

@api_router.post("/auth/redeem-promo")
async def redeem_promo_code(promo_data: PromoCodeRedeem, request: Request, user: dict = Depends(get_current_user)):
    """Redeem a promo code for permanent premium access"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if promo code is valid
    if promo_data.promoCode != FOUNDER_PROMO_CODE:
        raise HTTPException(status_code=400, detail="Code promo invalide")
    
    # Check if user already redeemed this code
    existing_redemption = await db.promo_redemptions.find_one({
        "userId": user["_id"],
        "promoCode": promo_data.promoCode
    })
    
    if existing_redemption:
        raise HTTPException(status_code=400, detail="Ce code promo a déjà été utilisé")
    
    # Update user to founder status (permanent premium)
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "isPremium": True,
                "isFounder": True,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    # Record promo code redemption
    redemption_doc = {
        "_id": str(uuid.uuid4()),
        "userId": user["_id"],
        "promoCode": promo_data.promoCode,
        "redeemedAt": datetime.utcnow()
    }
    await db.promo_redemptions.insert_one(redemption_doc)
    
    # Get updated limits
    updated_user = await db.users.find_one({"_id": user["_id"]})
    limits = await get_user_limits(updated_user, request)
    
    return {
        "success": True,
        "message": "Félicitations ! Vous avez maintenant un accès Founder permanent avec génération illimitée !",
        "limits": limits
    }

# QR Code Routes
@api_router.post("/qr/generate", response_model=QRResponse)
async def generate_qr_code(qr_data: QRCodeCreate, request: Request, user: dict = Depends(get_current_user)):
    # Validate URL
    if not validate_url(qr_data.url):
        raise HTTPException(status_code=422, detail="Invalid URL format")
    
    # Validate size
    if not validate_size(qr_data.size):
        raise HTTPException(status_code=422, detail="Invalid size format. Use format: 150x150 (50-1000 pixels)")
    
    # Check generation limits
    if not await check_generation_limit(user, request):
        limits = await get_user_limits(user, request)
        raise HTTPException(
            status_code=403, 
            detail=f"Generation limit reached. You have used {limits.used}/{limits.max} QR codes."
        )
    
    # Generate QR code URL
    from urllib.parse import quote
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size={qr_data.size}&data={quote(qr_data.url)}"
    
    # Create QR code document
    qr_id = str(uuid.uuid4())
    qr_doc = {
        "_id": qr_id,
        "userId": user["_id"] if user else None,
        "guestIp": request.client.host if not user else None,
        "url": qr_data.url,
        "qrCodeUrl": qr_code_url,
        "size": qr_data.size,
        "downloaded": False,
        "createdAt": datetime.utcnow()
    }
    
    await db.qr_codes.insert_one(qr_doc)
    
    # Update user QR count if authenticated
    if user:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$inc": {"qrCodeCount": 1}, "$set": {"updatedAt": datetime.utcnow()}}
        )
    
    # Create response
    qr_code = QRCode(
        id=qr_id,
        url=qr_data.url,
        qrCodeUrl=qr_code_url,
        size=qr_data.size,
        downloaded=False,
        createdAt=qr_doc["createdAt"]
    )
    
    # Get updated limits
    if user:
        updated_user = await db.users.find_one({"_id": user["_id"]})
        limits = await get_user_limits(updated_user, request)
    else:
        limits = await get_user_limits(None, request)
    
    return QRResponse(qrCode=qr_code, limits=limits)

@api_router.get("/qr/history", response_model=QRHistoryResponse)
async def get_qr_history(request: Request, user: dict = Depends(get_current_user)):
    # Build query based on user authentication
    if user:
        query = {"userId": user["_id"]}
    else:
        query = {"guestIp": request.client.host}
    
    # Get QR codes
    qr_docs = await db.qr_codes.find(query).sort("createdAt", -1).limit(50).to_list(50)
    
    qr_codes = [
        QRCode(
            id=doc["_id"],
            url=doc["url"],
            qrCodeUrl=doc["qrCodeUrl"],  
            size=doc["size"],
            downloaded=doc["downloaded"],
            createdAt=doc["createdAt"]
        )
        for doc in qr_docs
    ]
    
    limits = await get_user_limits(user, request)
    
    return QRHistoryResponse(qrCodes=qr_codes, limits=limits)

@api_router.delete("/qr/{qr_id}")
async def delete_qr_code(qr_id: str, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Delete QR code (only if owned by user)
    result = await db.qr_codes.delete_one({"_id": qr_id, "userId": user["_id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return {"success": True}

# Subscription Routes
@api_router.post("/subscription/upgrade")
async def upgrade_subscription(sub_data: SubscriptionUpgrade, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if user is already founder (permanent premium)
    if user.get("isFounder", False):
        raise HTTPException(status_code=400, detail="Vous avez déjà un accès Founder permanent")
    
    # Create subscription
    subscription_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=30)  # Monthly subscription
    
    subscription_doc = {
        "_id": subscription_id,
        "userId": user["_id"],
        "planType": sub_data.planType,
        "status": "active",
        "startDate": datetime.utcnow(),
        "expiresAt": expires_at,
        "createdAt": datetime.utcnow()
    }
    
    await db.subscriptions.insert_one(subscription_doc)
    
    # Update user premium status
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "isPremium": True,
                "subscriptionExpiresAt": expires_at,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    subscription = Subscription(
        id=subscription_id,
        planType=sub_data.planType,
        status="active",
        expiresAt=expires_at
    )
    
    limits = UserLimits(used=user.get("qrCodeCount", 0), max="unlimited", isPremium=True, isFounder=False)
    
    return {"subscription": subscription, "limits": limits}

@api_router.get("/subscription/status")
async def get_subscription_status(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    subscription = await db.subscriptions.find_one({
        "userId": user["_id"],
        "status": "active",
        "expiresAt": {"$gt": datetime.utcnow()}
    })
    
    limits = await get_user_limits(user, request)
    
    if subscription:
        sub_obj = Subscription(
            id=subscription["_id"],
            planType=subscription["planType"],
            status=subscription["status"],
            expiresAt=subscription["expiresAt"]
        )
        return {"subscription": sub_obj, "limits": limits}
    else:
        return {"subscription": None, "limits": limits}

# Health check
@api_router.get("/")
async def root():
    return {"message": "QR Code Generator API with Google OAuth & Founder Access", "version": "2.1.0"}

# Include the router in the main app
app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()