# Инфраструктура: Railway + Brevo + Cloudflare

## 1. Railway — деплой

1. Создай проект в [railway.app](https://railway.app)
2. Добавь сервис из GitHub репозитория (выбери этот репо)
3. Добавь **PostgreSQL** плагин → Railway автоматически выставит `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGPORT`
4. В разделе **Variables** сервиса добавь:
   ```
   LISTMONK_app__admin_username=admin
   LISTMONK_app__admin_password=<сильный пароль>
   LISTMONK_app__root_url=https://<твой домен>
   ```
5. Задеплой — Railway соберёт образ через `Dockerfile`

## 2. Cloudflare — домен

### DNS запись
В Cloudflare DNS добавь **CNAME**:
| Name       | Target                              | Proxy    |
|------------|-------------------------------------|----------|
| mail        | `<service>.up.railway.app`         | DNS only (серое облако) |

> **Важно:** ставь "DNS only" (не проксируй через Cloudflare). Railway сам выдаёт SSL через Let's Encrypt.
> Если хочешь оранжевое облако — в Cloudflare SSL/TLS → Overview установи режим **Full (strict)**.

### Custom Domain в Railway
1. Railway → Service → Settings → **Custom Domain**
2. Введи домен (например `mail.yourdomain.com`)
3. Railway покажет CNAME target — вставь его в Cloudflare DNS

## 3. Brevo — SMTP

1. Зайди в [app.brevo.com](https://app.brevo.com) → SMTP & API → SMTP
2. Сгенерируй SMTP key
3. Зайди в Listmonk: `https://<домен>` → **Settings → SMTP → Add server**

| Поле      | Значение                    |
|-----------|-----------------------------|
| Host      | `smtp-relay.brevo.com`      |
| Port      | `587`                       |
| Auth      | `LOGIN`                     |
| Username  | твой email в Brevo          |
| Password  | SMTP key из Brevo           |
| TLS       | STARTTLS                    |

4. В **Settings → General** выставь From email и From name
5. Отправь тестовое письмо — кнопка **Send test email**

## 4. Проверка

```
# health check
curl https://<домен>/api/health
# → {"data":{"status":"ok"}}
```
