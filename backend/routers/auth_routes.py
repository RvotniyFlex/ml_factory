import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.google_oauth import google
from backend.auth.jwt_manager import EXPIRE_HOURS, create_token, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])

bearer_scheme = HTTPBearer(auto_error=False)


@router.get("/google/login", summary="Запуск входа через Google OAuth2")
async def google_login(request: Request):
    """Редирект на страницу логина Google."""
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        raise HTTPException(500, "GOOGLE_REDIRECT_URI is not set")

    resp = await google.authorize_redirect(
        request,
        redirect_uri=redirect_uri,
        prompt="consent",
        access_type="offline",
    )
    return resp


@router.get(
    "/google/callback",
    name="google_callback",
    summary="Callback от Google, обмен кода на профайл + выдача JWT",
)
async def google_callback(request: Request):
    token = await google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or "email" not in userinfo:
        raise HTTPException(status_code=400, detail="Google auth failed")

    email = userinfo["email"]
    jwt_token = create_token(email, {"name": userinfo.get("name")})

    return JSONResponse(
        {
            "access_token": jwt_token,
            "email": email,
            "expires_in_hours": EXPIRE_HOURS,
        }
    )


@router.get("/debug/env")
def debug_env():
    import os

    return {
        "GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI"),
    }


@router.get("/me", summary="Проверка токена и получение клеймов")
def me(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = credentials.credentials
    try:
        claims = verify_token(token)
        return {"status": "ok", "claims": claims}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
