import os

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.auth.google_oauth import google
from backend.auth.jwt_manager import create_token, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")  # exact match with Google Console
    if not redirect_uri:
        raise HTTPException(500, "GOOGLE_REDIRECT_URI is not set")
    # опционально: prompt/access_type, чтобы было стабильнее в тестах
    return await google.authorize_redirect(
        request,
        redirect_uri=redirect_uri,
        prompt="consent",
        access_type="offline",
    )


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request):
    token = await google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or "email" not in userinfo:
        raise HTTPException(status_code=400, detail="Google auth failed")
    jwt_token = create_token(userinfo["email"], {"name": userinfo.get("name")})
    return JSONResponse({"access_token": jwt_token, "email": userinfo["email"]})


@router.get("/me")
def me(authorization: str = Header(...)):
    try:
        claims = verify_token(authorization)
        return {"status": "ok", "claims": claims}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
