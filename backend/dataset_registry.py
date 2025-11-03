upload_file(user_id, file_bytes, file_name) → data_id
проверяет лимит места

сохраняет файл в data_storage/{user_id}/{data_id}_{file_name}
возвращает data_id

delete_file(user_id, data_id)

load_dataframe(user_id, data_id) → pandas.DataFrame

get_storage_usage_mb(user_id) — сколько МБ занимает папка пользователя
хранит лимит MAX_STORAGE_MB