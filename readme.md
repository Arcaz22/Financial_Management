# 🤖 Bot Telegram Financial Management

## 🗂️ Structure Directori
```
├── app/
│   ├── core/
│   ├── router/
│   ├── schema/
│   ├── service/
│   ├── utils/
├── cloudflared/
│   ├── tunnelID.json
│   ├── config.yml
├── venv/
├── main.py
├── requirements.txt
├── docker-compose.yml
└── .env
```

## 🛠️ Config

1. config.yml
    ```sh
    tunnel: <Tunnel ID>
    credentials-file: /etc/cloudflared/<Tunnel ID>.json
    protocol: http2

    ingress:
    - hostname: domain
    service: service
    - service: http_status:404
    ```
2. Run cloudflared local
    ```sh
    docker run -d \
    --name cloudflared \
    -v $(pwd)/cloudflared:/etc/cloudflared \
    cloudflare/cloudflared:latest tunnel run
    ```
3. If you want use docker-compose for cloudflared
    ```sh
    version: '3.8'

    services:
    cloudflared:
        image: cloudflare/cloudflared:latest
        container_name: cloudflared
        restart: always
        command: tunnel run
        volumes:
        - ./cloudflared:/etc/cloudflared
    ```
3. Environtment
    ```sh
    TELEGRAM_BOT_TOKEN=bot token
    BASE_WEBHOOK_URL=https://domain
    ```

## 🚀 Run Bot

1. Runnng Fast Api
    ```sh
    uvicorn main:app --host 0.0.0.0 --reload
    ```
2. Doc Api
    ```sh
    https://domain.docs
    ```
