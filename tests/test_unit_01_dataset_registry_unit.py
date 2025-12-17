"""
Unit тесты для сервиса dataset_registry с моками S3.
"""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from backend.dataset_registry import (
    delete_file,
    get_storage_usage_mb,
    load_dataframe,
    upload_file,
)
from utils.settings import settings


@pytest.fixture
def mock_s3_client():
    """
    Фикстура для создания мока S3 клиента.
    Возвращает функцию-фабрику, которая создает мок клиента.
    Мок клиент переиспользуется для проверки вызовов.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    async def _create_mock_client():
        return mock_client

    _create_mock_client.mock_client = mock_client
    return _create_mock_client


@pytest.fixture
def mock_s3_client_with_data():
    """
    Фикстура с предустановленными данными для S3 клиента.
    Симулирует наличие файлов в хранилище.
    Мок клиент переиспользуется для проверки вызовов.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_list_response = {
        "Contents": [
            {
                "Key": "users/test_user/datasets/file1.parquet",
                "Size": 1024 * 1024,
            },  # 1 MB
            {
                "Key": "users/test_user/datasets/file2.parquet",
                "Size": 512 * 1024,
            },  # 0.5 MB
        ]
    }
    mock_client.list_objects_v2 = AsyncMock(return_value=mock_list_response)

    mock_client.put_object = AsyncMock(return_value={"ETag": "test-etag"})

    mock_client.delete_object = AsyncMock(return_value={})

    mock_body = MagicMock()
    test_df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    parquet_bytes = test_df.to_parquet()
    mock_body.read = AsyncMock(return_value=parquet_bytes)
    mock_get_response = {"Body": mock_body}
    mock_client.get_object = AsyncMock(return_value=mock_get_response)

    async def _create_mock_client():
        return mock_client

    _create_mock_client.mock_client = mock_client
    return _create_mock_client


@pytest.mark.asyncio
async def test_get_storage_usage_mb_with_fixture(mock_s3_client_with_data):
    """
    Тест получения размера хранилища с использованием фикстуры.
    Использует фикстуру mock_s3_client_with_data для мока S3.
    """
    s3_client_factory = mock_s3_client_with_data
    user_id = "test_user"

    result = await get_storage_usage_mb(user_id, s3_client_factory)

    assert result == pytest.approx(1.5, rel=0.01)

    mock_client = s3_client_factory.mock_client
    mock_client.list_objects_v2.assert_called_once()
    call_args = mock_client.list_objects_v2.call_args
    assert call_args.kwargs["Prefix"] == f"users/{user_id}/"


@pytest.mark.asyncio
async def test_get_storage_usage_mb_empty_storage():
    """
    Тест получения размера хранилища для пустого хранилища (без фикстуры).
    Создает мок напрямую в тесте.
    """

    async def mock_s3_factory():
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_client.list_objects_v2 = AsyncMock(return_value={})

        return mock_client

    user_id = "empty_user"
    result = await get_storage_usage_mb(user_id, mock_s3_factory)

    assert result is None


@pytest.mark.asyncio
async def test_upload_file_success():
    """
    Тест успешной загрузки файла.
    Создает мок напрямую в тесте.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_client.list_objects_v2 = AsyncMock(return_value={})

    mock_client.put_object = AsyncMock(return_value={"ETag": "test-etag"})

    async def s3_factory():
        return mock_client

    user_id = "test_user"
    file_bytes = b"test file content" * 1000  # Небольшой файл
    file_name = "test.csv"

    result = await upload_file(user_id, file_bytes, file_name, s3_factory)

    assert result is not None
    assert isinstance(result, str)

    mock_client.put_object.assert_called_once()
    call_args = mock_client.put_object.call_args
    assert call_args.kwargs["Bucket"] == settings.s3_bucket
    assert "users/test_user/datasets/" in call_args.kwargs["Key"]
    assert call_args.kwargs["Body"] == file_bytes


@pytest.mark.asyncio
async def test_upload_file_storage_limit_exceeded():
    """
    Тест загрузки файла при превышении лимита хранилища.
    Создает мок напрямую в тесте.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_list_response = {
        "Contents": [
            {"Key": "users/test_user/datasets/file1.parquet", "Size": 199 * 1024 * 1024}
        ]
    }
    mock_client.list_objects_v2 = AsyncMock(return_value=mock_list_response)

    async def s3_factory():
        return mock_client

    user_id = "test_user"
    file_bytes = b"x" * (5 * 1024 * 1024)
    file_name = "large_file.csv"

    result = await upload_file(user_id, file_bytes, file_name, s3_factory)

    assert result is None


@pytest.mark.asyncio
async def test_delete_file_success():
    """
    Тест успешного удаления файла.
    Создает мок напрямую в тесте.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_list_response = {
        "Contents": [
            {"Key": "users/test_user/datasets/test_data_id.parquet", "Size": 1024}
        ]
    }
    mock_client.list_objects_v2 = AsyncMock(return_value=mock_list_response)

    mock_client.delete_object = AsyncMock(return_value={})

    async def s3_factory():
        return mock_client

    user_id = "test_user"
    data_id = "test_data_id"

    result = await delete_file(user_id, data_id, s3_factory)

    assert result == data_id

    mock_client.delete_object.assert_called_once()


@pytest.mark.asyncio
async def test_delete_file_not_found():
    """
    Тест удаления несуществующего файла.
    Создает мок напрямую в тесте.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_client.list_objects_v2 = AsyncMock(return_value={})

    async def s3_factory():
        return mock_client

    user_id = "test_user"
    data_id = "non_existent_id"

    result = await delete_file(user_id, data_id, s3_factory)

    assert result is None


@pytest.mark.asyncio
async def test_load_dataframe_success():
    """
    Тест успешной загрузки DataFrame из S3.
    Создает мок напрямую в тесте.
    """
    test_df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    parquet_bytes = test_df.to_parquet()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_list_response = {
        "Contents": [
            {"Key": "users/test_user/datasets/test_data_id.parquet", "Size": 1024}
        ]
    }
    mock_client.list_objects_v2 = AsyncMock(return_value=mock_list_response)

    mock_body = MagicMock()
    mock_body.read = AsyncMock(return_value=parquet_bytes)
    mock_get_response = {"Body": mock_body}
    mock_client.get_object = AsyncMock(return_value=mock_get_response)

    async def s3_factory():
        return mock_client

    user_id = "test_user"
    data_id = "test_data_id"

    result = await load_dataframe(user_id, data_id, s3_factory)

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert list(result.columns) == ["col1", "col2"]
    pd.testing.assert_frame_equal(result, test_df)


@pytest.mark.asyncio
async def test_load_dataframe_not_found():
    """
    Тест загрузки несуществующего DataFrame.
    Создает мок напрямую в тесте.
    """
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_client.list_objects_v2 = AsyncMock(return_value={})

    async def s3_factory():
        return mock_client

    user_id = "test_user"
    data_id = "non_existent_id"

    result = await load_dataframe(user_id, data_id, s3_factory)

    assert result is None
