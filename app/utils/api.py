import httpx


async def telegram_post(url: str, data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()


async def telegram_get(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
