# ChorvaBor Backend

ChorvaBor — chorva mollari va uy hayvonlari e'lonlari mobil ilovasi uchun backend loyihasi.

## Xususiyatlar

- Telefon raqami + SMS OTP orqali autentifikatsiya
- Kategoriyalar bo'yicha hayvon e'lonlari, rasm/video bilan
- Xarita bo'yicha qidiruv (radius asosida)
- Sevimlilar, obuna (follow), Reels
- Real-time xabar almashish (WebSocket)
- Bildirishnomalar, shikoyat tizimi
- To'liq API hujjatlari (Swagger/OpenAPI)

## Texnologiyalar

- Django REST Framework
- PostgreSQL
- Redis
- JWT autentifikatsiya (SimpleJWT)
- WebSocket (Django Channels)
- uv (paket menejeri)

## Loyiha strukturasi

```text
/
├── apps/                # Django ilovasi (models, serializers, views, services, tests, urls)
├── root/                # Loyiha sozlamalari (settings, wsgi, asgi)
└── .github/workflows/   # CI/CD (GitHub Actions)
```

## API Endpointlar

| Guruh                | Endpoint                                           |
|:---------------------|:---------------------------------------------------|
| **Auth**             | `/auth/request-otp/`, `/auth/verify-otp/`          
|                      | `/auth/refresh/`, `/auth/me/`                      
| **Listings & Reels** | `/listings/`, `/reels/`                            
|                      | `/categories/`, `/favorites/`, `/reports/`         
|                      | `/listings/map/`                                   
| **User**             | `/users/<id>/`, `/users/<id>/follow/`              
| **Chat**             | `/conversations/`, `/conversations/<id>/messages/` 
| **Notifications**    | `/notifications/`, `/notifications/<id>/read/`     

## Ishga tushirish (Development)

```bash
uv sync
cp .env.example .env  # yoki .env faylini qo'lda yarating (SECRET_KEY, DB_*, REDIS_URL)
# Migratsiya fayllari repo'da saqlanmaydi — birinchi marta quyidagilarni bajaring:
uv run python manage.py makemigrations && uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Testlar va CI

Testlarni ishga tushirish buyrug'i:

```bash
uv run pytest apps/tests/
```

Har bir Pull Request va Push qilinganda GitHub Actions platformasida testlar va linting (ruff) avtomatik ravishda ishga
tushadi.

## Real-time chat (WebSocket)

Suhbatdoshlar o'rtasida real-time muloqot `ws://<host>/ws/chat/<conversation_id>/` WebSocket manzili orqali amalga
oshiriladi. Ulanishda foydalanuvchi suhbat ishtirokchisi ekanligi tekshiriladi.
