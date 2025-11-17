import os

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from starlette.config import Config

load_dotenv()

config = Config(environ=os.environ)

oauth = OAuth(config)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
