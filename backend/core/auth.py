import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
import httpx
from dotenv import load_dotenv

load_dotenv()

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_JWKS_URL = "https://faithful-urchin-60.clerk.accounts.dev/.well-known/jwks.json"

# Cache for JWKS
jwks_cache = None

async def get_jwks():
    global jwks_cache
    if jwks_cache is None:
        print("Fetching JWKS from Clerk...")
        async with httpx.AsyncClient() as client:
            response = await client.get(CLERK_JWKS_URL)
            response.raise_for_status()
            jwks_cache = response.json()
        print("JWKS fetched and cached.")
    return jwks_cache

async def verify_clerk_jwt(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> str:
    if not CLERK_SECRET_KEY:
        print("CLERK_SECRET_KEY not configured in backend/.env")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="CLERK_SECRET_KEY not configured")

    token = credentials.credentials
    print(f"Verifying JWT...: {token}")
    print(f"Received JWT: {token[:30]}...") # Log first 30 chars of token
    try:
        # Get the unverified headers to extract the key ID (kid)
        unverified_headers = jwt.get_unverified_headers(token)
        kid = unverified_headers.get("kid")
        print(f"Unverified headers: {unverified_headers}, KID: {kid}")

        if not kid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing kid")

        # Fetch JWKS and find the key matching the kid
        jwks = await get_jwks()
        
        key = None
        for jwk_key in jwks["keys"]:
            if jwk_key["kid"] == kid:
                key = jwk_key
                break
        
        if not key:
            print(f"Public key with KID {kid} not found in JWKS.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: public key not found")

        # Decode and verify the token
        payload = jwt.decode(
            token,
            key, # Pass the public key dictionary
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_aud": False, # Clerk's audience can vary, verify manually if needed
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
            }
        )
        print(f"JWT successfully decoded. Payload: {payload}")

        user_id = payload.get("sub") # 'sub' claim usually contains the user ID
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: user ID not found")
        print(f"Authenticated user ID: {user_id}")

        return user_id

    except jwt.ExpiredSignatureError:
        print("JWT expired.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTError as e:
        print(f"JWT verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials: {e}")
    except Exception as e:
        print(f"Unexpected error during JWT verification: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")