from typing import Dict, Any, Optional
import json, asyncio
try:
    import redis.asyncio as redis
except Exception:
    redis = None

_client = None

async def get_client(url: str | None):
    global _client
    if not url or redis is None: return None
    if _client is None: _client = redis.from_url(url, decode_responses=True)
    return _client

async def cache_set(session_id: str, state: Dict[str, Any], ttl_sec: int = 86400, url: str | None = None):
    client = await get_client(url)
    if not client: return
    await client.setex(f"state:{session_id}", ttl_sec, json.dumps(state))

async def cache_get(session_id: str, url: str | None = None) -> Optional[Dict[str, Any]]:
    client = await get_client(url)
    if not client: return None
    s = await client.get(f"state:{session_id}")
    return json.loads(s) if s else None
