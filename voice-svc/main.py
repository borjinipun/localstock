import os
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from adapters import get_adapter
from dialog import build_flows, schedule_flows

app = FastAPI(title="localstock-voice-svc", version="0.1.0")

SERVICE_TOKEN = os.environ.get("SERVICE_TOKEN", "dev-service-token")
DEFAULT_PROVIDER = os.environ.get("PROVIDER_TELEPHONY", "mock")
VTS_INTERNAL_URL = os.environ.get("API_INTERNAL_URL", "http://localhost:8000/api/internal/verification/update/")


class ShopSchema(BaseModel):
    id: int
    name: str
    phone: str
    language: str = "hi"
    mock_behavior: str = "always_yes"


class CallRequest(BaseModel):
    target_id: int
    attempt_id: int
    shop: ShopSchema
    item_intent: dict = Field(default_factory=dict)
    languages: list[str] = ["hi", "en"]
    channels: list[str] = ["whatsapp", "call"]
    callback_url: str = VTS_INTERNAL_URL
    callback_token: str = SERVICE_TOKEN


def _check(token: str):
    if token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="bad service token")


@app.get("/health")
def health():
    return {"ok": True, "service": "voice-svc", "provider": DEFAULT_PROVIDER}


@app.post("/v1/calls", status_code=202)
async def create_call(req: CallRequest, x_service_token: str = Header(default="")):
    """Start a verification contact; the adapter schedules lifecycle webhooks.
    Idempotent per attempt_id: repeat calls replace (never double-fire) the flow."""
    _check(x_service_token)
    adapter = get_adapter(DEFAULT_PROVIDER)
    flows = adapter.flows(req.shop.mock_behavior, req.channels,
                          req.item_intent, req.target_id, req.attempt_id)
    call_id = f"call_{uuid.uuid4().hex[:12]}"
    schedule_flows([(d, {**payload, "call_id": call_id}) for d, payload in flows],
                   req.callback_url, req.callback_token)
    return {"call_id": call_id, "status": "scheduled_flow",
            "behaviour": req.shop.mock_behavior,
            "flows": [{"delay_seconds": d, "outcome": p.get("outcome")} for d, p in flows]}
