# GigaChat migration

Что изменено:
- генеративная модель по умолчанию переведена на `GigaChat`;
- в интерфейсе доступны `GigaChat`, `GigaChat-2-Pro` и `GigaChat-2-Max`;
- эмбеддинговая модель по умолчанию заменена на бесплатную `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
- cross-encoder исправлен на рабочую бесплатную модель `cross-encoder/ms-marco-MiniLM-L-6-v2`;
- добавлена авторизация GigaChat через `GIGACHAT_AUTH_KEY` с автоматическим получением access token.

Новые переменные окружения backend:

```env
GIGACHAT_AUTH_KEY=ваш_base64_ключ_авторизации_из_кабинета_GigaChat_API
# либо вместо строки выше:
# GIGACHAT_ACCESS_TOKEN=ваш_готовый_access_token

GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_AUTH_URL=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
GIGACHAT_API_URL=https://gigachat.devices.sberbank.ru/api/v1/chat/completions
GIGACHAT_VERIFY_SSL=false

DEFAULT_MODEL=GigaChat
DEFAULT_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

Примечание:
- `GIGACHAT_VERIFY_SSL=false` оставлен для упрощённого локального запуска. Для production лучше установить корневой сертификат Минцифры и включить проверку SSL.
