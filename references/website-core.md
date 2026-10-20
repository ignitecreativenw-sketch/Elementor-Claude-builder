# Website Core — the only way the kit connects to a site

Website Core (v1.1.0+) is Adam's WordPress plugin: one JSON endpoint, short-lived keys with a read or write scope, no admin password, no SSH, no Application Password, no browser import. Every site write in this kit goes through it. The older routes (WP-CLI over SSH, core REST, browser import) are retired; their scripts sit in `deploy/legacy/` for reference only.

Client: `deploy/push_core.py` (direct HTTP, no dependencies). The plugin's own instructions are the source of truth for field names; this file maps them to the playbook.

## Connecting

- Endpoint `POST {site}/wp-json/website-core/v1/push`; if that 404s, `POST {site}/?rest_route=/website-core/v1/push` (the client tries both).
- Header `X-Core-Key: wck_…` (Bearer also works but some Apache hosts strip it). Body is JSON with an `action` field.
- Health check without a key: `GET {site}/wp-json/website-core/v1/ping`.
- HTTPS required. If the cloud workspace is blocked by the org proxy, run the same command on Adam's Mac; never retry from the cloud.

## Keys

The site owner's wp-admin → Tools › Website Core produces a "Copy for AI" block (site URL, endpoint, key). Scopes: **read** (status, find, sample, meta, option, images, log, rotate) or **write** (everything). A key expires on its own; the plugin itself expires 30 days after activation unless the owner sets a date.

Lifecycle, which is skill rule 9 in practice:

1. The pasted key is used **once**: `CORE_KEY=<pasted> python3 deploy/push_core.py --rotate`. The reply carries the new key; the client writes it to `$WEBSITE_CORE_HOME/<host>.key` (chmod 600) and the pasted one dies after the grace period (default 10 minutes), so the copy in the chat history is useless.
2. **Where the rotated key may live:** the key file on Adam's Mac, `deploy/.env` on Adam's Mac (gitignored), or **the Claude Project for that client**, so any chat in the project can see and use it without Adam pasting it again. A project is private to Adam, so this is allowed; a chat reply, a shared file, the kit repo, the build report or a memory file is not. Rotate again whenever a key may have leaked.
3. Nothing in the kit prints a key. `status` output is saved to `reference/status.json` with the key field removed.
4. Errors: `core_forbidden` wrong key (check the header, never guess); `core_key_expired` ask Adam for a new key; `core_scope` read key used for a write; `core_expired` plugin expired (Adam re-activates); `core_method` use POST; `core_duplicate` two items share a title, pass `id`; `core_locked` 10 bad attempts, wait 15 minutes. The client stops on all of these; it retries only 5xx and network errors.

## Mandatory first steps, every site

`rotate` → `status` → `sample` an existing page or template → tell Adam what was found and what will change before any large write. `status` gives WP/Elementor/Pro versions, theme, SEO plugin, front page, menus and locations, page templates, post types, existing templates with conditions, key scope and expiry, and whether the site runs containers. `sample` is the schema ground truth: container vs section layout, settings keys, `version`, `__globals__` usage.

## Action per stage

| Stage | Actions | Notes |
|---|---|---|
| 0 Intake | `rotate`, `status` | Replaces the SSH/app-password questions. Host profile still records nginx/Apache and cache layer. |
| 1 Site setup | `sample` → `reference/sample-<id>.json`; `kit` (merged into the active kit: `system_colors`, `system_typography`, `container_width`; sample the kit id from status first); `settings` (title, tagline, timezone, permalinks, `search_visible:false` on staging, site icon); `fonts` (woff2 → `uploads/core-fonts/`) + `snippet` or kit custom CSS for `@font-face`; `plugins` list/deactivate; `option` for allow-listed reads | The mu-plugin still goes up by SFTP: the plugin installs nothing. Yoast-REST registration in the mu-plugin is unused; SEO rides on `page`. |
| 4 Build | — | JSON written as sent, no validation. Element ids: unique hex, `elType` container/widget, `settings`, `elements`, `widgetType`. Images as `{"url","id"}` from the media reply. Match the sampled layout. |
| 6 Push | `media` (base64 or URL, alt/title/caption, reused by name unless `replace`; JPEG/PNG auto-converted to WebP, so always use the returned url), `page` (slug/id, title, content, template from `status.page_templates`, status, parent slug, `seo`, `featured_image`, `elementor_settings`, `set_front`), `template` (header/footer/single/archive/popup/loop-item/… with `conditions` like `include/general`, `include/singular/page/12`, `exclude/singular/front_page`), `conditions` to verify, `menu` (nested items to page/post/term/url, `location`, `replace`), `flush` | `push_core.py <tpl> "<Title>" <slug> [parent]` = auditors → media → regenerate → page → flush. Several pages: `--batch ops.json` (≤ 50 ops, in order; rotate/batch/selfdestruct not allowed inside). |
| 8 SEO | `page` with `seo` {title, description, focus_keyword, canonical, noindex, og_image} from `spec/seo/<slug>.json` (mapped to Yoast / Rank Math / SEOPress); `terms` for categories/tags; `meta` to read back; `post` for blog posts (drafts unless status given) | A write that doesn't read back is a failed write. |
| 9 Perf | `images` (`status: not_optimised|heavy`, by size) to find weight; `convert` only when Adam asks (dry run first, DB backup advised on live); `flush` after every change | |
| 10/11 | `settings` (`search_visible:true` at go-live, `front_page`), `trash` for placeholder pages (bin only), then `selfdestruct` with `confirm:true` **only on Adam's explicit go-ahead** (`CONFIRM_SELFDESTRUCT=yes`), or Adam removes the plugin | Never leave it on a live site. |
| 12 Retro | `log` (recent requests) into the retro evidence | |

## Hard limits

No plugin/theme installs or file edits (mu-plugin by SFTP). No SVG uploads (logo SVGs by SFTP or the Icon widget's library). Fonts aren't registered in Elementor's list (`@font-face` via kit CSS or a snippet). No users, passwords, comments. No permanent delete; media never deleted (except `convert … delete_originals` which needs Adam's go-ahead). Protected `_` meta refused unless allow-listed; WooCommerce prices refused. Widgets/Customizer read-only. Settings only from an allow-list (no registration, roles, URLs, admin email, licences). Max upload 20 MB.

## Rules the client enforces

Rotate first; key never printed. Read before write: `status`, then `find`/`sample`; never overwrite a page or template not identified by id or slug; prefer `id` once known. Never `selfdestruct`, `convert`, delete originals, switch themes or deactivate plugins without Adam's explicit go-ahead. Report ids, URLs and every warning in a response. If something fails twice, stop and explain; don't loop.

## Hosting gotchas

Cloudflare Flexible SSL → use Full SSL. Apache may strip `Authorization` → `X-Core-Key` is what we send. Plain permalinks → `?rest_route=` form. Low-traffic sites run WP-Cron late. Bot protection still applies to the cloud container's IP; the Mac is the clean IP. After any write: `flush`, purge the host cache, wait 25 s, warm twice, then measure.
