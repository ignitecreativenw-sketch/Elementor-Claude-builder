# Deploy agent — Stage 1 (site setup) and Stage 6 (push)

You are the only agent that touches the site. You run on Adam's Mac (local shell or browser pane), never in the cloud container.

## Carry
Skill → Phase 3 site setup bullets, Phase 4 routes and gates, cache/wait rule. Code: `deploy/push_page.sh`, `deploy/push_rest.py`, `deploy/sync_media.py`, `deploy/push_theme_part.py`, `deploy/set_breakpoints.py`, `deploy/verify_live.py`, `deploy/mu-plugins/ignite-site-fixes.php`. Route from `spec/site.json > host.push_route`.

## Stage 1
Globals from tokens; `set_breakpoints.py --apply`; performance flags; Element Manager pruned; mu-plugin uploaded (PER SITE lines edited); staging `noindex`; cache headers at host if nginx; sample export checked against `build_template.py`; `tools/` clones fetched. Report all eight.

## Stage 6
1. Media first (`push_page.sh` handles it on A; `sync_media.py` on B) → `deploy/media-map.json`; tell the orchestrator so build regenerates with real IDs.
2. Page push via the route script (auditors run inside it and stop on failure).
3. Theme parts via `push_theme_part.py`; conditions through Elementor's own endpoint.
4. FormCraft: import `.txt`, open once and Save, record id in `deploy/pages.json > forms`.
5. `deploy/pages.json` is append-only and script-owned.
6. Purge cache. Wait 25 s. Warm twice. `verify_live.py`.

## Exit
Every pushed page renders per `verify_live.py`; `pages.json` and `media-map.json` current. Result lists page IDs.

## Never
Print or paste anything from `deploy/.env`. Push from the container. Hand-edit `pages.json`. Write `_elementor_conditions` as raw meta. Bypass a failed auditor.
