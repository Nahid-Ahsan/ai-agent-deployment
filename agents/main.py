from fastapi import FastAPI, Security
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer
from api.routes import router as travel_router
from api.user_routes import router as user_router
import uvicorn
import os

app = FastAPI(title="Travel Booking Multi-Agent API")

# Define OAuth2 scheme for token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# Define HTTP Bearer scheme for manual token validation
security = HTTPBearer()

# Include API routes
app.include_router(travel_router)
app.include_router(user_router)

# Optional: Add global security requirement (uncomment to enforce on all endpoints)
# app.add_middleware(
#     Security(security)
# )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)