"""Make ad-hoc requests through the rotating proxy, the way recording does.

This exists so debugging a plugin against a live site never means writing a
throwaway script: the proxy wiring, .env loading, and IP rotation are the same
ones the recording fixture uses (`tests.plugins.proxy`), so what you see here is
what a `--record-mode=rewrite` run will see.

Run it through the project venv so `requests` and the proxy creds resolve:

    uv run --env-file .env python -m tests.plugins.probe https://api.gofile.io/accounts -X POST
    uv run python -m tests.plugins.probe "https://gofile.io/dist/js/config.js" --no-proxy

Exit nodes are flaky, so a request is retried across fresh IPs (--tries) until
one connects. Use --no-proxy to hit the site directly.
"""

import argparse
import sys

import requests

from tests.plugins.proxy import credentials, missing_creds, proxy_url


def _pairs(values: list[str], sep: str) -> dict[str, str]:
    """Split repeated 'key<sep>value' flags into a dict, sep-agnostic on spaces."""
    out: dict[str, str] = {}
    for item in values:
        key, _, value = item.partition(sep)
        out[key.strip()] = value.strip()
    return out


def _request(args: argparse.Namespace) -> requests.Response:
    headers = _pairs(args.header, ":")
    cookies = (
        _pairs(args.cookie, ":")
        if any(":" in c for c in args.cookie)
        else _pairs(args.cookie, "=")
    )
    params = _pairs(args.param, "=")
    headers.setdefault("User-Agent", args.user_agent)

    proxies = None
    if not args.no_proxy:
        creds = credentials()
        if missing := missing_creds(creds):
            sys.exit(f"missing proxy credentials: {missing} (use --no-proxy to skip)")

    last_error: Exception | None = None
    for attempt in range(1, args.tries + 1):
        if not args.no_proxy:
            url = proxy_url(creds)
            proxies = {"http": url, "https": url}
        try:
            return requests.request(
                args.method,
                args.url,
                params=params or None,
                headers=headers,
                cookies=cookies or None,
                data=args.data,
                proxies=proxies,
                timeout=args.timeout,
            )
        except requests.RequestException as exc:
            last_error = exc
            print(f"  attempt {attempt}/{args.tries} failed: {exc}", file=sys.stderr)
    sys.exit(f"all {args.tries} attempts failed: {last_error}")


def _print_response(response: requests.Response, preview: int) -> None:
    print(f"{response.status_code} {response.reason}  via {response.url}")
    for key in ("content-type", "server", "cf-ray", "location"):
        if value := response.headers.get(key):
            print(f"  {key}: {value}")
    print("-" * 60)
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        import json

        print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:preview])
    else:
        print(response.text[:preview])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url")
    parser.add_argument("-X", "--method", default="GET")
    parser.add_argument(
        "-H", "--header", action="append", default=[], help="'Key: value'"
    )
    parser.add_argument(
        "-b",
        "--cookie",
        action="append",
        default=[],
        help="'name: value' or 'name=value'",
    )
    parser.add_argument(
        "-p", "--param", action="append", default=[], help="'key=value' query param"
    )
    parser.add_argument("-d", "--data", default=None, help="raw request body")
    parser.add_argument("--no-proxy", action="store_true", help="hit the site directly")
    parser.add_argument(
        "-n", "--tries", type=int, default=5, help="retry across fresh IPs"
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--preview", type=int, default=2000, help="response body chars to print"
    )
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )
    args = parser.parse_args(argv)

    _print_response(_request(args), args.preview)


if __name__ == "__main__":
    main()
