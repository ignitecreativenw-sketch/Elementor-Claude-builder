#!/usr/bin/env bash
# Push a generated Elementor template to the target site over SSH + WP-CLI.
# No GitHub: assets and JSON are scp'd up from this Mac, then written with WP-CLI.
#
#   ./push_page.sh home "Home" home
#            $1 template   $2 page title   $3 slug
#
# Configure once:
set -euo pipefail
SSH_HOST="${SSH_HOST:-REPLACE-ME}"          # e.g. user@ssh.stackcp.com
SSH_PORT="${SSH_PORT:-22}"
WP_PATH="${WP_PATH:-REPLACE-ME}"            # e.g. /home/sites/xx/s/site.co.uk/public_html
REMOTE_TMP="${REMOTE_TMP:-/tmp/ecb}"

TPL="${1:-home}"
TITLE="${2:-Home}"
SLUG="${3:-home}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."

wp() { ssh -p "$SSH_PORT" "$SSH_HOST" "cd $WP_PATH && wp $*"; }

echo "==> 1/5  ship assets + template"
ssh -p "$SSH_PORT" "$SSH_HOST" "mkdir -p $REMOTE_TMP/assets"
scp -P "$SSH_PORT" -q "$ROOT"/assets/*.webp "$SSH_HOST:$REMOTE_TMP/assets/"
scp -P "$SSH_PORT" -q "$ROOT/templates/$TPL.json" "$SSH_HOST:$REMOTE_TMP/$TPL.json"

echo "==> 2/5  import media (skips anything already in the library)"
ssh -p "$SSH_PORT" "$SSH_HOST" "cd $WP_PATH && bash -s" <<REMOTE > "$ROOT/deploy/media-import.tsv"
set -e
for f in $REMOTE_TMP/assets/*.webp; do
  name=\$(basename "\$f")
  existing=\$(wp post list --post_type=attachment --name="\${name%.webp}" --field=ID --posts_per_page=1 2>/dev/null | head -1)
  if [ -n "\$existing" ]; then
    id=\$existing
  else
    id=\$(wp media import "\$f" --porcelain)
  fi
  url=\$(wp post get \$id --field=guid)
  printf '%s\t%s\t%s\n' "\$name" "\$id" "\$url"
done
REMOTE

echo "==> 3/5  rebuild media-map.json and regenerate the template with real ids"
python3 - "$ROOT" <<'PY'
import json, sys, os, csv
root = sys.argv[1]
m = {}
with open(os.path.join(root, "deploy", "media-import.tsv")) as f:
    for row in csv.reader(f, delimiter="\t"):
        if len(row) == 3:
            m[row[0]] = {"id": int(row[1]), "url": row[2]}
# carry alt text over from the asset manifest
man = json.load(open(os.path.join(root, "assets", "manifest.json")))
alts = {os.path.splitext(a["file"])[0] + ".webp": a["alt"] for a in man}
for k in m:
    m[k]["alt"] = alts.get(k, "")
json.dump(m, open(os.path.join(root, "deploy", "media-map.json"), "w"), indent=1)
print(f"   media-map.json: {len(m)} attachments")
PY
python3 "$ROOT/build/build_template.py" "$TPL"
scp -P "$SSH_PORT" -q "$ROOT/templates/$TPL.json" "$SSH_HOST:$REMOTE_TMP/$TPL.json"

echo "==> 4/5  create or update the page"
PAGES_JSON="$ROOT/deploy/pages.json"
[ -f "$PAGES_JSON" ] || echo '{}' > "$PAGES_JSON"
ID=$(python3 -c "import json,sys;print(json.load(open('$PAGES_JSON')).get('$SLUG',''))")
if [ -z "$ID" ]; then
  ID=$(wp post create --post_type=page --post_title="'$TITLE'" --post_name="$SLUG" \
        --post_status=draft --porcelain)
  python3 - "$PAGES_JSON" "$SLUG" "$ID" <<'PY'
import json, sys
p, slug, pid = sys.argv[1:]
d = json.load(open(p)); d[slug] = pid.strip(); json.dump(d, open(p, "w"), indent=1)
PY
  echo "   created page $ID"
else
  echo "   updating page $ID"
fi

ssh -p "$SSH_PORT" "$SSH_HOST" "cd $WP_PATH && bash -s" <<REMOTE
set -e
wp post meta update $ID _elementor_edit_mode builder
wp post meta update $ID _elementor_template_type wp-page
wp post meta update $ID _elementor_version "\$(wp plugin get elementor --field=version)"
wp post meta update $ID _wp_page_template elementor_canvas
wp post meta update $ID _elementor_data "\$(jq -c .content $REMOTE_TMP/$TPL.json)"
wp elementor flush-css
REMOTE

echo "==> 5/5  purge cache"
wp cache flush || true
ssh -p "$SSH_PORT" "$SSH_HOST" "cd $WP_PATH && wp stackcache purge 2>/dev/null || true"
echo "done — page $ID (/$SLUG), now purge StackCache in My20i if the CLI purge was a no-op"
