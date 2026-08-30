import asyncio
from typing import Optional
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.utils.stream_logs import get_logs

router = APIRouter(prefix="/api/stream", tags=["stream"])

@router.get("/logs")
async def stream_logs(since_id: Optional[str] = None):
    async def event_generator():
        last_id = since_id
        while True:
            # Check for new logs
            new_logs = get_logs(last_id)
            if new_logs:
                for log in new_logs:
                    yield {
                        "event": "log",
                        "id": log["id"],
                        "data": log
                    }
                last_id = new_logs[-1]["id"]
            
            # Polling delay
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
