from __future__ import annotations

from pathlib import Path

import yaml


EXPECTED_ROUTES = {
    "mail": {
        "rule": "PathPrefix(`/mail/`)",
        "service": "mail-service",
        "middleware": "strip-mail",
        "prefix": "/mail",
        "url": "http://mail-service:8701",
    },
    "tts": {
        "rule": "PathPrefix(`/tts/`)",
        "service": "tts-proxy",
        "middleware": "strip-tts",
        "prefix": "/tts",
        "url": "http://tts-proxy:8700",
    },
    "aa": {
        "rule": "PathPrefix(`/aa/`)",
        "service": "aa-proxy",
        "middleware": "strip-aa",
        "prefix": "/aa",
        "url": "http://aa-proxy:8702",
    },
    "api": {
        "rule": "PathPrefix(`/api/v1`)",
        "service": "registrar",
        "middleware": None,
        "prefix": None,
        "url": "http://registrar:8709",
    },
    "web-ui": {
        "rule": "PathPrefix(`/`)",
        "service": "web-ui",
        "middleware": None,
        "prefix": None,
        "url": "http://web-ui:80",
    },
}


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_traefik_routes(path: Path) -> list[str]:
    config = _load_yaml(path)
    http = config.get("http", {})
    routers = http.get("routers", {})
    middlewares = http.get("middlewares", {})
    services = http.get("services", {})
    errors: list[str] = []

    for route_name, expected in EXPECTED_ROUTES.items():
        router = routers.get(route_name)
        if router is None:
            errors.append(f"missing router: {route_name}")
            continue
        if router.get("rule") != expected["rule"]:
            errors.append(f"router {route_name} rule mismatch: {router.get('rule')}")
        if router.get("service") != expected["service"]:
            errors.append(f"router {route_name} service mismatch: {router.get('service')}")
        middleware = expected["middleware"]
        router_middlewares = router.get("middlewares", []) or []
        if middleware is not None:
            if middleware not in router_middlewares:
                errors.append(f"router {route_name} missing middleware: {middleware}")
            prefixes = (
                middlewares.get(middleware, {}).get("stripPrefix", {}).get("prefixes", [])
            )
            if expected["prefix"] not in prefixes:
                errors.append(
                    f"middleware {middleware} missing prefix: {expected['prefix']}"
                )
        # A route that is not declared with a strip-* middleware in
        # EXPECTED_ROUTES must not pull in any strip-* middleware, even if
        # it still applies rate-limit/retry/etc. This catches accidental
        # new strip middleware on a route that should pass paths through.
        if middleware is None:
            for mw in router_middlewares:
                if mw.startswith("strip-"):
                    errors.append(
                        f"router {route_name} unexpectedly uses strip middleware: {mw}"
                    )
        service = services.get(expected["service"], {})
        servers = service.get("loadBalancer", {}).get("servers", [])
        urls = {server.get("url") for server in servers}
        if expected["url"] not in urls:
            errors.append(f"service {expected['service']} missing upstream: {expected['url']}")

    return errors


def main() -> int:
    errors = validate_traefik_routes(Path("traefik/traefik.yml"))
    if errors:
        print("Traefik route validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Traefik route validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
