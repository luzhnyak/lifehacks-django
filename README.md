# Lifehacks Django

Україномовний сайт із категоріями та дописами. Python 3.12+, Django 5.2 LTS,
SQLite для локальної розробки. Редагування через Django Admin.

## Локальний запуск (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DJANGO_DEBUG = 'true'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

На Linux/macOS: `python3 -m venv .venv`, `source .venv/bin/activate`,
`export DJANGO_DEBUG=true`, далі використовуйте `python manage.py ...`.

`.env.example` описує змінні середовища. Django **не читає `.env` автоматично**:
встановлюйте змінні в оболонці або через менеджер процесів. Скрипт SSH-деплою
окремо завантажує серверний `.env`, який має бути довіреним shell-файлом.

## Перевірки

```powershell
$env:DJANGO_DEBUG = 'true'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py collectstatic --dry-run --noinput
```

Тести використовують окрему БД і тимчасове сховище завантажень.
CI виконує перевірки перед SSH-деплоєм; pull request не запускає деплой.

## Налаштування production

`DJANGO_DEBUG` за замовчуванням вимкнений. Для запуску обов'язкові:

- `DJANGO_SECRET_KEY`: новий випадковий секрет, збережений поза Git.
  Старий ключ із репозиторію потрібно замінити; це завершить чинні сесії.
- `DJANGO_ALLOWED_HOSTS=lifehacks.in.ua,www.lifehacks.in.ua`.
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://lifehacks.in.ua,https://www.lifehacks.in.ua`.

Згенерувати секрет: `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
У shell-файлі `.env` беріть значення секретів у лапки. Захистіть файл від
читання іншими користувачами. Менеджер процесів повинен отримувати ті самі змінні,
що й команди керування Django.

HTTPS-перенаправлення, secure cookies та HSTS увімкнені для production.
`DJANGO_TRUST_PROXY_HTTPS=true` дозволяється лише за проксі, який видаляє
клієнтський `X-Forwarded-Proto` і сам встановлює коректне значення. Інакше
підроблений заголовок може обійти перевірку HTTPS. Перевірте конфігурацію проксі
перед запуском, щоб уникнути циклу перенаправлень.
HSTS для піддоменів і preload навмисно вимкнені; `DJANGO_SECURE_HSTS_SECONDS`
можна встановити у `0` під час первинного налаштування HTTPS.

## Оновлення наявного сервера

1. Зробіть резервну копію БД і медіафайлів. Перевірте Python 3.12+.
2. Налаштуйте секрет, хости та HTTPS у середовищі сервісу **до оновлення коду**.
3. Для старих завантажень у `static/media` встановіть `DJANGO_MEDIA_ROOT`
   на абсолютний шлях до цієї папки. Або скопіюйте їх у нову `media/` і
   перевірте доступність файлів перед перемиканням. Відносні імена файлів у БД
   не змінюються.
4. Налаштуйте вебсервер: `/static/` → `staticfiles/`, `/media/` → `MEDIA_ROOT`.
   Django обслуговує медіа лише локально при `DEBUG=true`.
5. Встановіть залежності, виконайте `python manage.py check --deploy`,
   `python manage.py migrate --noinput` і `python manage.py collectstatic --noinput`.
6. Перезапустіть WSGI/ASGI-сервіс через наявний менеджер процесів і перевірте сайт.
   Назва сервісу в репозиторії відсутня, тому workflow не виконує його перезапуск.

`main/static/` — вихідні ресурси; `staticfiles/` —
результат `collectstatic`; `media/` — нові завантаження. Старі медіафайли
не потрапляють у `collectstatic`. Не запускайте `makemigrations` на сервері:
застосовуйте міграції, які зберігаються в Git.

HTML дописів очищується через `nh3` під час відображення: звичайне форматування
зберігається, скрипти, обробники подій і небезпечні URL видаляються. Довільні
iframe/style також можуть бути видалені; YouTube вставляється окремим полем.
Поточні URL і наявні slug дописів збережені.

Докладний перелік виправлень та обмежень: [docs/review.md](docs/review.md).
