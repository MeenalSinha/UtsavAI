from openapi_spec_validator import validate

from app.database.pool import Database
from app.main import create_app
from tests.conftest import build_settings


def test_generated_openapi_schema_is_valid_and_matches_phase0_contract():
    settings = build_settings()
    schema = create_app(settings, database=Database(settings)).openapi()
    validate(schema)
    paths = schema["paths"]
    assert set(paths["/api/v1/events"]) == {"get", "post"}
    assert set(paths["/api/v1/events/{event_id}"]) == {"get", "patch", "delete"}
    assert set(paths["/api/v1/me"]) == {"get", "patch"}
    assert "get" in paths["/api/v1/health"] and "get" in paths["/api/v1/health/ready"]
    patch_params = {p["name"] for p in paths["/api/v1/events/{event_id}"]["patch"]["parameters"]}
    assert "if-match" in {p.lower() for p in patch_params}
    assert paths["/api/v1/events"]["post"]["responses"]["201"]
    assert paths["/api/v1/events/{event_id}"]["delete"]["responses"]["204"]
