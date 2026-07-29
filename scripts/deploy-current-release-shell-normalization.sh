#!/usr/bin/env bash
# Atomically normalize the current Base2026 release shell without rebuilding or
# replacing its current daily data/content. Source assets remain local and are
# copied only into a temporary remote staging source directory.
set -Eeuo pipefail

SSH_HOST="${SSH_HOST:-geo}"
REMOTE_BASE="${REMOTE_BASE:-/var/www/base2026-knowledge}"
RELEASE_NAME="${1:?usage: $0 <release-name>}"
# Default to the exact current release inventory. Callers may pin EXPECTED_PAGES
# only after independently verifying that count for a frozen target.
EXPECTED_PAGES="${EXPECTED_PAGES:-}"
LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ROOT="${LOCAL_ROOT}/.tmp-shell-normalization-source-${RELEASE_NAME}"
REMOTE_SOURCE="/tmp/${RELEASE_NAME}-shell-source"

case "$RELEASE_NAME" in (*[!A-Za-z0-9._-]*|'') echo "Unsafe release name" >&2; exit 64;; esac
trap 'rm -rf "$SOURCE_ROOT"' EXIT

mkdir -p "$SOURCE_ROOT/scripts" "$SOURCE_ROOT/templates/shared"
cp "$LOCAL_ROOT/scripts/normalize-wordpress-v4-shell-release.py" "$SOURCE_ROOT/scripts/"
cp "$LOCAL_ROOT/scripts/wordpress-v4-header.css" "$SOURCE_ROOT/scripts/"
cp "$LOCAL_ROOT/scripts/wordpress-v4-footer.css" "$SOURCE_ROOT/scripts/"
cp "$LOCAL_ROOT/scripts/wordpress-v4-header.js" "$SOURCE_ROOT/scripts/"
cp "$LOCAL_ROOT/templates/shared/alex-home-v4-header.html" "$SOURCE_ROOT/templates/shared/"
cp "$LOCAL_ROOT/templates/shared/alex-home-v4-footer.html" "$SOURCE_ROOT/templates/shared/"
cp "$LOCAL_ROOT/templates/shared/wordpress-personal-shell-sources.json" "$SOURCE_ROOT/templates/shared/"

ssh "$SSH_HOST" "set -Eeuo pipefail
base='$REMOTE_BASE'
current=\"\$(readlink -f \"\$base/current\")\"
case \"\$current\" in \"\$base\"/releases/*) ;; *) echo unsafe-current-target >&2; exit 70;; esac
test -d \"\$current\"
test -f \"\$current/web/index.html\"
test ! -e \"\$base/releases/$RELEASE_NAME\"
rm -rf '$REMOTE_SOURCE'
mkdir -p '$REMOTE_SOURCE'"

scp -r "$SOURCE_ROOT/." "$SSH_HOST:$REMOTE_SOURCE/"

ssh "$SSH_HOST" "REMOTE_BASE='$REMOTE_BASE' RELEASE_NAME='$RELEASE_NAME' REMOTE_SOURCE='$REMOTE_SOURCE' EXPECTED_PAGES='$EXPECTED_PAGES' bash -s" <<'REMOTE'
set -Eeuo pipefail
base="$REMOTE_BASE"
release="$RELEASE_NAME"
source_root="$REMOTE_SOURCE"
expected_pages="$EXPECTED_PAGES"
current_link="$base/current"
previous_link="$base/previous"
current_target="$(readlink -f "$current_link")"
release_dir="$base/releases/$release"
staging_dir="$base/releases/.$release.staging.$$"
current_tmp="$base/.current.$release.$$"
previous_tmp="$base/.previous.$release.$$"
switched=0

cleanup() {
  rm -rf "$staging_dir"
  rm -f "$current_tmp" "$previous_tmp"
  rm -rf "$source_root"
}
rollback_on_error() {
  status=$?
  trap - ERR
  set +e
  if [ "$switched" = 1 ]; then
    rollback_tmp="$base/.current.rollback.$$"
    ln -s "$current_target" "$rollback_tmp" && mv -Tf "$rollback_tmp" "$current_link"
    nginx -t && systemctl reload nginx && systemctl is-active --quiet nginx
    echo "ROLLBACK_COMPLETE=$current_target" >&2
  fi
  cleanup
  exit "$status"
}
trap cleanup EXIT
trap rollback_on_error ERR

case "$current_target" in "$base"/releases/*) ;; *) echo unsafe-current-target >&2; exit 70;; esac
test -d "$current_target"
if [ -z "$expected_pages" ]; then
  expected_pages="$(find "$current_target/web" -type f -name '*.html' -print | wc -l | tr -d '[:space:]')"
fi
case "$expected_pages" in ''|*[!0-9]*) echo invalid-expected-pages >&2; exit 71;; esac
test "$expected_pages" -gt 0
test ! -e "$release_dir"

mkdir -p "$staging_dir"
cp -a "$current_target/." "$staging_dir/"
python3 "$source_root/scripts/normalize-wordpress-v4-shell-release.py" \
  --release-root "$staging_dir" \
  --expected-pages "$expected_pages" \
  --asset-version "$release" \
  --report "$staging_dir/wordpress-personal-shell-report.json"
python3 - "$staging_dir/wordpress-personal-shell-report.json" "$expected_pages" <<'PY'
import json, sys
report=json.load(open(sys.argv[1], encoding='utf-8'))
expected=int(sys.argv[2])
assert report['passed'] is True, report
assert report['failure_count'] == 0, report
assert report['normalized_pages'] == expected, report
assert report['body_fingerprint_count'] == expected, report
print('SHELL_NORMALIZATION_PASS=' + str(report['normalized_pages']))
PY

mv "$staging_dir" "$release_dir"
ln -s "$current_target" "$previous_tmp"
mv -Tf "$previous_tmp" "$previous_link"
ln -s "$release_dir" "$current_tmp"
mv -Tf "$current_tmp" "$current_link"
switched=1
nginx -t
systemctl reload nginx
systemctl is-active --quiet nginx
test "$(readlink -f "$current_link")" = "$release_dir"
switched=0
printf 'PREVIOUS_TARGET=%s\nCURRENT_TARGET=%s\n' "$current_target" "$release_dir"
REMOTE
