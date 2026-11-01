"""API behaviour that must hold before any SQL runs."""

import uuid

from tests.conftest import auth

BASE = "/api/v1"


def test_health_is_public_and_leaks_no_configuration(offline_client):
    r = offline_client.get(f"{BASE}/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"status", "service", "version"}
    assert "database" not in r.text.lower() and "postgres" not in r.text.lower()


def test_meta_is_public_and_exposes_central_config(offline_client):
    body = offline_client.get(f"{BASE}/meta").json()
    assert body["default_currency"] == "INR"
    assert {t["key"]: t["enabled"] for t in body["event_types"]}["wedding"] is True
    assert "archived" in body["event_statuses"]
    assert "archived" not in body["patchable_statuses"]


def test_security_headers_and_request_id(offline_client):
    r = offline_client.get(f"{BASE}/health", headers={"X-Request-ID": "client-req-12345"})
    assert r.headers["x-request-id"] == "client-req-12345"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert r.headers["cache-control"] == "no-store"
    bad = offline_client.get(f"{BASE}/health", headers={"X-Request-ID": "bad id with spaces!!"})
    assert bad.headers["x-request-id"].startswith("req_")


def test_unauthenticated_requests_get_401_envelope(offline_client):
    for method, path in [
        ("get", "/me"),
        ("patch", "/me"),
        ("get", "/events"),
        ("post", "/events"),
        ("get", f"/events/{uuid.uuid4()}"),
        ("patch", f"/events/{uuid.uuid4()}"),
        ("delete", f"/events/{uuid.uuid4()}"),
    ]:
        r = getattr(offline_client, method)(f"{BASE}{path}")
        assert r.status_code == 401, (method, path)
        err = r.json()["error"]
        assert err["code"] == "UNAUTHENTICATED"
        assert err["request_id"] == r.headers["x-request-id"]


def test_tampered_and_expired_tokens_get_401(offline_client, make_token):
    import time

    expired = make_token(exp=int(time.time()) - 600)
    assert offline_client.get(f"{BASE}/me", headers=auth(expired)).status_code == 401
    assert offline_client.get(f"{BASE}/me", headers=auth("abc.def.ghi")).status_code == 401
    wrong_scheme = {"Authorization": f"Basic {make_token()}"}
    assert offline_client.get(f"{BASE}/me", headers=wrong_scheme).status_code == 401


def test_user_id_header_is_not_an_identity_source(offline_client):
    r = offline_client.get(f"{BASE}/me", headers={"X-User-Id": str(uuid.uuid4())})
    assert r.status_code == 401


def test_validation_error_uses_documented_envelope(offline_client, make_token):
    body = {
        "title": "Bad dates",
        "start_at": "2027-02-14T10:00:00+05:30",
        "end_at": "2027-02-12T10:00:00+05:30",
        "timezone": "Asia/Kolkata",
    }
    r = offline_client.post(f"{BASE}/events", json=body, headers=auth(make_token()))
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert err["message"] == "The event date range is invalid."
    assert err["request_id"]
    assert "input" not in r.text.lower().replace("invalid", "")  # no echo of submitted values


def test_multiple_field_errors_listed(offline_client, make_token):
    r = offline_client.post(
        f"{BASE}/events",
        json={
            "title": "",
            "start_at": "x",
            "end_at": "y",
            "timezone": "Nope",
            "expected_guest_count": -5,
        },
        headers=auth(make_token()),
    )
    assert r.status_code == 422
    fields = {f["field"] for f in r.json()["error"]["details"]["fields"]}
    assert {"title", "start_at", "end_at", "timezone", "expected_guest_count"} <= fields


def test_malformed_json_is_400(offline_client, make_token):
    r = offline_client.post(
        f"{BASE}/events",
        content="{not json",
        headers={**auth(make_token()), "Content-Type": "application/json"},
    )
    assert r.status_code == 400 and r.json()["error"]["code"] == "INVALID_REQUEST"


def test_patch_without_if_match_is_428(offline_client, make_token):
    r = offline_client.patch(
        f"{BASE}/events/{uuid.uuid4()}", json={"title": "New"}, headers=auth(make_token())
    )
    assert r.status_code == 428 and r.json()["error"]["code"] == "PRECONDITION_REQUIRED"


def test_oversized_body_rejected(offline_client, make_token):
    r = offline_client.post(
        f"{BASE}/events",
        content="x" * 200_000,
        headers={**auth(make_token()), "Content-Type": "application/json"},
    )
    assert r.status_code == 413 and r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_unknown_route_uses_envelope(offline_client):
    r = offline_client.get(f"{BASE}/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_cors_only_for_configured_origin(offline_client):
    ok = offline_client.options(
        f"{BASE}/events",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-credentials" not in ok.headers
    bad = offline_client.options(
        f"{BASE}/events",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in bad.headers
