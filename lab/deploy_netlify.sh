#!/bin/sh
# Put AIT at https://ai-tribe.netlify.app — one page and two functions, nothing else.
#
# Cost, measured and the reason for the two modes: a *production* deploy costs 15 of the account's 300
# monthly credits, so twenty of them spend the month and the site pauses. Preview deploys are free.
# Therefore the default is a preview, which gives its own URL for testing, and `--prod` promotes.
#
#     ./lab/deploy_netlify.sh          # a preview URL, free, for working
#     ./lab/deploy_netlify.sh --prod   # the real address, 15 credits
#
# Why a separate copy of the page exists at all: the site publishes a directory, and the directory must
# contain nothing but the app. Publishing the repository would serve tests, members and workflows at
# their own paths, and the app's address would double as a file browser.
#
# The site belongs to the founder's free Netlify team (lindsayridgeway / Aoede). Nothing here is
# load-bearing: the tribe lives in the repository, so if this site disappears every tribe is untouched
# and the page can be served from anywhere.
set -e
cd "$(dirname "$0")/.."
site=5f4150cb-113b-4816-aad2-7d195df8bc8b
prod=0
[ "$1" = "--prod" ] && prod=1

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/pub" "$work/fn"
cp ait.html "$work/pub/index.html"
printf 'User-agent: *\nDisallow: /\n' > "$work/pub/robots.txt"
# Anyone who appends ait.html out of habit gets the app, not a 404, and keeps their ?tribe=.
printf '/ait.html  /  200\n' > "$work/pub/_redirects"
cp site/functions/*.js "$work/fn/"

msg="ait.html $(git rev-parse --short HEAD)"
if [ "$prod" = "1" ]; then
  netlify deploy --prod --dir "$work/pub" --functions "$work/fn" --site "$site" --message "$msg"
else
  netlify deploy --dir "$work/pub" --functions "$work/fn" --site "$site" --message "$msg"
fi
