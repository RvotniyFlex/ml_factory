import os
import subprocess

from sync_service.s3_connector import s3_client_factory
from utils.logger import get_logger, setup_logging

BUCKET = os.environ["DVC_SYNC_S3_BUCKET"]
PREFIX = os.environ.get("DVC_SYNC_S3_PREFIX")
LOCAL_DATA_ROOT = os.environ.get("DVC_SYNC_LOCAL_DATA_ROOT")
BRANCH = os.environ.get("DVC_SYNC_BRANCH")
REPO_ROOT = os.environ.get("REPO_ROOT")
FULL_DATA_ROOT = os.path.join(REPO_ROOT, LOCAL_DATA_ROOT)
REMOTE_BUCKET = os.environ.get("REMOTE_BUCKET")

s3_client_factory = s3_client_factory()

setup_logging()
logger = get_logger("sync")


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Выполняет команду в терминале внутри корня репозитория.

    Args:
        cmd (list[str]): Команда и её аргументы.
        check (bool): Если True — выбрасывает исключение при ненулевом коде возврата.

    Returns:
        result (subprocess.CompletedProcess): Результат выполнения команды.
    """
    logger.info(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT, check=check, capture_output=False)


def git(*args) -> subprocess.CompletedProcess:
    """
    Выполняет команду git в терминале внутри корня репозитория.
    """
    return run(["git", *args])


def dvc(*args) -> subprocess.CompletedProcess:
    """
    Выполняет команду dvc в терминале внутри корня репозитория.
    """
    return run(["dvc", *args])


def git_has_changes() -> bool:
    """
    Проверяет наличие изменений в репозитории.

    Returns:
        result (bool): True, если есть изменения, иначе False.
    """
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    result: bool = bool(proc.stdout.strip())
    return result


def list_s3_parquet_keys() -> list[str]:
    """
    Возвращает список ключей S3, соответствующих parquet-файлам.

    Returns:
        keys (set[str]): Список ключей S3.
    """
    keys: list = []
    params: dict = {"Bucket": BUCKET}  # , "Prefix": PREFIX}

    with s3_client_factory() as client:
        resp: dict = client.list_objects_v2(**params)

    logger.info(f'Contents: {resp.get("Contents", [])}')

    for obj in resp.get("Contents", []):
        key: str = obj["Key"]
        if key.endswith(".parquet"):
            keys.append(key)

    logger.info("11111")
    logger.info(f"Найдено: {len(keys)} файлов parquet в S3")
    return keys


def list_local_tracked() -> dict[str, str]:
    """
    Возвращает словарь локальных файлов, отслеживаемых dvc.

    Returns:
        mapping (dict[str, str]): Словарь, где ключи — это ключи S3, а значения — локальные пути.
    """
    mapping: dict = {}
    if not os.path.exists(FULL_DATA_ROOT):
        return mapping

    for dirpath, _, filenames in os.walk(FULL_DATA_ROOT):
        for f in filenames:
            if not f.endswith(".parquet"):
                continue
            local_path: str = os.path.join(dirpath, f)

            rel: str = os.path.relpath(local_path, FULL_DATA_ROOT)
            s3_key: str = rel.replace(os.sep, "/")
            mapping[s3_key] = local_path

    logger.info(f"Найдено: {len(mapping)} путей к файлам dvc")
    return mapping


def s3_key_to_local_path(key: str) -> str:
    """
    Возвращает локальный путь для указанного ключа S3.

    Args:
        key (str): Ключ S3.

    Returns:
        local_path (str): Локальный путь.
    """
    return os.path.join(FULL_DATA_ROOT, key)


def ensure_bucket_exists(bucket: str) -> None:
    """
    Создает S3-бакет, если он не существует.

    Args:
        bucket (str): Название S3-бакета.
    """

    with s3_client_factory() as client:
        try:
            client.head_bucket(Bucket=bucket)
            logger.info(f"Бакет: '{bucket}' найден")
        except Exception:
            logger.info(f"Бакет: '{bucket}' не существует")
            client.create_bucket(Bucket=bucket)
            logger.info(f"Бакет: '{bucket}' создан.")


def main() -> None:
    """
    Основной цикл синхронизации S3 → локальная директория → DVC → Git.

    * Проверяет существование DVC-хранилища (бакета) и создаёт его при необходимости.
    * Получает список файлов из S3 и список уже локально отслеживаемых файлов.
    * Определяет новые и удалённые файлы.
        Для новых файлов:
            - скачивает файл из S3 через временный S3-клиент,
            - сохраняет в локальное зеркало,
            - добавляет файл под DVC-управление.
        Для удалённых файлов:
            - удаляет .dvc-файл,
            - удаляет локальную копию.
    Если есть изменения:
        - делает git add + commit,
        - пушит данные в DVC remote,
        - пушит изменения в GitHub.
    """
    logger.info("2222")

    ensure_bucket_exists(REMOTE_BUCKET)
    os.makedirs(FULL_DATA_ROOT, exist_ok=True)

    s3_keys = list_s3_parquet_keys()
    local_map = list_local_tracked()

    new_files = s3_keys - local_map.keys()
    removed_files = local_map.keys() - s3_keys

    logger.info(f"Новый файлы: {len(new_files)}")
    logger.info(f"Удаленные файлы: {len(removed_files)}")

    for key in sorted(new_files):
        local_path = s3_key_to_local_path(key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        logger.info(f"Добавляем: {BUCKET}/{key} -> {local_path}")
        with s3_client_factory() as client:
            client.download_file(BUCKET, key, local_path)
        dvc("add", local_path)

    for key in sorted(removed_files):
        local_path = local_map[key]
        dvc_file = local_path + ".dvc"

        logger.info(f"Удаляем: {local_path}")
        if os.path.exists(dvc_file):
            dvc("remove", dvc_file)
        if os.path.exists(local_path):
            os.remove(local_path)

    if git_has_changes():
        git("add", ".")
        git("commit", "-m", "Sync S3 → DVC (auto)")
        dvc("push")
        git("push", "origin", BRANCH)
        logger.info("Запушил изменения")
    else:
        logger.info("Нет изменений")


if __name__ == "__main__":
    main()
