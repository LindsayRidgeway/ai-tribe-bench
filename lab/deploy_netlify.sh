#!/bin/sh
# Put AIT at https://ai-tribe.netlify.app — one file, nothing else.
#
# Why a separate copy of the file exists at all: the site publishes a directory, and the directory
# must contain nothing but the app. Publishing the repository would serve tests, members and
# workflows at their own paths, and the app's address would double as a file browser.
#
# The site belongs to the founder's free Netlify team (lindsayridgeway / Aoede). It is one of three
# dead-simple hosts that could serve this page; the other two are GitHub Pages, which already does,
# and the file on a disk. Nothing here is load-bearing: the tribe lives in the repository, so if
# this site disappears every tribe is untouched and the page can be served from anywhere.
set -e
cd "$(dirname "$0")/.."
site=5f4150cb-113b-4816-aad2-7d195df8bc8b
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp ait.html "$tmp/index.html"
printf 'User-agent: *\nDisallow: /\n' > "$tmp/robots.txt"
# Anyone who appends ait.html out of habit gets the app, not a 404, and keeps their ?tribe=.
printf '/ait.html  /  200\n' > "$tmp/_redirects"
netlify deploy --prod --dir "$tmp" --site "$site" \
  --message "ait.html $(git rev-parse --short HEAD)"
