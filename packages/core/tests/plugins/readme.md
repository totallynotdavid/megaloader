# plugin suite

One vcr module per plugin. Each test drives the real plugin through the public
`extract()` engine and snapshots the normalized result. The same test runs in
two modes:

- **replay (default):** plays the committed cassette offline and compares
  against the `.ambr` snapshot. Deterministic, no network, no credentials. This
  is the PR gate (`test.yml`, run with `--block-network`).
- **record / drift (`--record-mode=rewrite`):** re-fetches from the live site
  through the proxy. Refreshing cassettes and catching "the platform changed"
  are the same action; the scheduled run (`live.yml`) does this and a snapshot
  mismatch is the drift signal.

A cassette is real network truth with an expiry date. The scheduled drift run is
what renews it, so replaying one offline is faithful, not invented.

## Where each kind of test lives

- **`tests/unit/`** parsing and crypto (`parse_target`, `parse_api_posts`,
  `deobfuscate_video_url`) and error handling driven by `fake_fetcher`
  (`test_faults.py`). Hand-written inputs are legitimate here because the
  input's *shape* is the thing under test.
- **`tests/plugins/` (here)** full traversal and assembly against recorded
  responses. Hand-written fixtures are not allowed: a happy path must replay a
  real recording or it is just asserting what we imagined the site returns.

## The proxy

`conftest.py` routes recording through Geonode, one fresh IP per test (per
fixture URL). A model that fans out into many page requests spreads across IPs
to dodge rate limits, while a single auth flow stays pinned to one IP. The proxy
is dormant during replay and mandatory during recording: missing `GEONODE_*`
credentials fail the run rather than hammering bare egress.

## Recording (maintainers)

Run these from `packages/core` (or use `mise run test-record`, which loads
`.env` and uses the full path from the repo root):

```sh
# Refresh every cassette and snapshot from live:
uv run pytest tests/plugins --record-mode=rewrite --snapshot-update

# One plugin (auth plugins also need their session secret exported):
PIXIV_PHPSESSID=... uv run pytest tests/plugins/test_pixiv.py \
  --record-mode=rewrite --snapshot-update
```

Credentials come from the project-root `.env` (or the environment). Cookies and
auth tokens are scrubbed before a cassette is written, so recordings are safe to
commit. `normalize.py` strips the query string from download URLs so signed CDN
params do not show up as false drift. Commit the regenerated cassettes and
`.ambr` snapshots together; the snapshot diff is the reviewable artifact.

## Adding a plugin

1. Add fixture URLs to `../test_urls.py`.
2. Create `test_<plugin>.py`: mark tests `@pytest.mark.vcr`, call `extract()`,
   assert the items are valid, then `normalize_items(items) == snapshot`.
3. Record once with `--record-mode=rewrite --snapshot-update`, then verify the
   replay passes offline.

Prefer small fixtures: a model that walks hundreds of detail pages makes a huge,
brittle cassette. Cover that pagination logic with a `fake_fetcher` unit test
and point the cassette at a small album or a single item instead.
