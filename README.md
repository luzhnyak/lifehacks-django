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

`.env.example` описує змінні середовища. Django автоматично читає `.env` у корені
проєкту через `python-dotenv`, зокрема під час запуску Gunicorn через Supervisor.
Змінні середовища процесу мають пріоритет. Скрипт SSH-деплою також завантажує цей
файл, тому використовуйте прості рядки `KEY=value` без shell-команд і підстановок.

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
читання іншими користувачами. Користувач процесу Gunicorn повинен мати право
читання `.env`; файл з правами `600` має належати саме цьому користувачу.

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
6. Workflow автоматично виконує `sudo -n supervisorctl restart lifehacks.in.ua`
   після успішних перевірок, міграцій і collectstatic. Якщо перезапуск не вдасться,
   деплой завершиться помилкою.

Одноразово дозвольте SSH-користувачу з GitHub Secret `SERVER_USER` перезапускати
цей процес без пароля. Знайдіть шлях командою `command -v supervisorctl`,
відкрийте `sudo visudo -f /etc/sudoers.d/lifehacks-deploy` і додайте правило
(замініть `DEPLOY_USER` та шлях на фактичні):

```sudoers
DEPLOY_USER ALL=(root) NOPASSWD: /usr/bin/supervisorctl restart lifehacks.in.ua
```

`-n` забороняє sudo чекати пароль у CI. Правило дозволяє лише цю команду
для цього процесу. Після збереження від імені SSH-користувача перевірте
`sudo -n supervisorctl restart lifehacks.in.ua` — команда перезапустить сайт.

При `ERROR (spawn error)` подивіться конкретну помилку:

```bash
sudo supervisorctl status lifehacks.in.ua
sudo supervisorctl tail lifehacks.in.ua stderr
sudo supervisorctl tail lifehacks.in.ua stdout
```

Переконайтеся, що Supervisor запускає Gunicorn із того самого `venv`, куди
встановлені залежності. `.env` повинен лежати поруч із `manage.py`.
Експорт змінних у SSH-сеансі не передає їх вже запущеному Supervisor.

`main/static/` — вихідні ресурси; `staticfiles/` —
результат `collectstatic`; `media/` — нові завантаження. Старі медіафайли
не потрапляють у `collectstatic`. Не запускайте `makemigrations` на сервері:
застосовуйте міграції, які зберігаються в Git.

HTML дописів очищується через `nh3` під час відображення: звичайне форматування
зберігається, скрипти, обробники подій і небезпечні URL видаляються. Довільні
iframe/style також можуть бути видалені; YouTube вставляється окремим полем.
Поточні URL і наявні slug дописів збережені.

Докладний перелік виправлень та обмежень: [docs/review.md](docs/review.md).
