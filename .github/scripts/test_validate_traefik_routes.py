from pathlib import Path

from validate_traefik_routes import EXPECTED_ROUTES, validate_traefik_routes


def test_validate_traefik_routes_accepts_root_contract():
    errors = validate_traefik_routes(Path("traefik/traefik.yml"))
    assert errors == []


def test_expected_routes_cover_public_services():
    assert set(EXPECTED_ROUTES) == {"mail", "tts", "aa", "api", "web-ui"}
