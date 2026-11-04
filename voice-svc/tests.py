"""voice-svc unit tests: behavior→outcome mapping + API happy path (docs 03)."""

from dialog import build_flows
from fastapi.testclient import TestClient

from main import app


def test_always_yes_flow_confirmed():
    flows = build_flows("always_yes", ["call", "whatsapp"],
                        {"color": "Blue", "size": "M"}, 11, 22)
    assert len(flows) == 1
    delay, payload = flows[0]
    assert payload["outcome"] == "CONFIRMED_IN_STOCK"
    assert payload["channel"] == "call"
    assert "M" in payload["sizes"]
    assert delay > 0


def test_wa_only_uses_whatsapp():
    _, payload = build_flows("wa_only_yes", ["whatsapp"], {"color": "Blue", "size": "M"}, 1, 2)[0]
    assert payload["channel"] == "whatsapp"
    assert payload["outcome"] == "CONFIRMED_IN_STOCK"


def test_unreachable_and_never_answer_maps_to_UNREACHABLE():
    _, payload = build_flows("unreachable", ["call"], {}, 1, 2)[0]
    assert payload["outcome"] == "UNREACHABLE"
    _, payload = build_flows("never_answer", ["call", "whatsapp"], {}, 1, 2)[0]
    assert payload["outcome"] == "UNREACHABLE"


def test_no_with_alternative():
    _, payload = build_flows("no_with_alternative", ["call"], {"color": "Blue", "size": "M"}, 1, 2)[0]
    assert payload["outcome"] == "ALTERNATIVE_OFFERED"
    assert payload["condition_text"].startswith("Black")


def test_api_schedules_flow():
    client = TestClient(app)
    res = client.post("/v1/calls", json={
        "target_id": 5, "attempt_id": 9,
        "shop": {"id": 1, "name": "Style Studio", "phone": "919000000001", "mock_behavior": "always_yes"},
        "item_intent": {"color": "Blue", "size": "M"},
        "languages": ["hi", "en"],
        "callback_url": "http://api:8000/api/internal/verification/update/",
        "callback_token": "dev-service-token",
    }, headers={"X-Service-Token": "dev-service-token"})
    assert res.status_code == 202, res.text
    assert res.json()["status"] == "scheduled_flow"
    assert res.json()["behaviour"] == "always_yes"


def test_api_rejects_bad_token():
    client = TestClient(app)
    # with a valid body, a bad token is rejected as 401
    res = client.post("/v1/calls", json={
        "target_id": 5, "attempt_id": 9,
        "shop": {"id": 1, "name": "S", "phone": "919000000001"},
    }, headers={"X-Service-Token": "wrong"})
    assert res.status_code == 401, res.text
