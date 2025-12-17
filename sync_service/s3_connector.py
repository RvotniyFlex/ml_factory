import os
from contextlib import contextmanager

from boto3.session import Session
from botocore.config import Config

REGION = os.environ.get("AWS_REGION")
KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_ENDPOINT_URL = os.environ.get("DVC_ENDPOINT_URL")


def s3_client_factory() -> callable:
    """
    Фабрика, возвращающая функцию-контекстный менеджер, создающий S3-клиента.
    """

    def _make_session():
        return Session(
            aws_access_key_id=KEY_ID,
            aws_secret_access_key=ACCESS_KEY,
            region_name=REGION,
        )

    cfg = Config(signature_version="s3v4")

    @contextmanager
    def _client():
        session = _make_session()
        client = session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            config=cfg,
        )
        try:
            yield client
        finally:
            client.close()

    return _client
