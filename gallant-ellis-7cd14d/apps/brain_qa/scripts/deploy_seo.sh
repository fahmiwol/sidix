#!/bin/bash
set -e
cd /opt/sidix

echo "=== PULL LATEST ==="
git pull origin main 2>&1 | tail -3

echo ""
echo "=== SYNC LANDING SEO ASSETS ==="
cp -v /opt/sidix/SIDIX_LANDING/index.html /www/wwwroot/sidixlab.com/index.html
cp -v /opt/sidix/SIDIX_LANDING/robots.txt /www/wwwroot/sidixlab.com/robots.txt
cp -v /opt/sidix/SIDIX_LANDING/sitemap.xml /www/wwwroot/sidixlab.com/sitemap.xml
cp -v /opt/sidix/SIDIX_LANDING/manifest.json /www/wwwroot/sidixlab.com/manifest.json

echo ""
echo "=== VERIFY SEO URLS ==="
for path in robots.txt sitemap.xml manifest.json og-image.png; do
    STATUS=$(curl -sI "https://sidixlab.com/$path" | head -1 | awk '{print $2}')
    echo "  $path → HTTP $STATUS"
done

echo ""
echo "=== VERIFY JSON-LD count ==="
COUNT=$(curl -s https://sidixlab.com/ | grep -c 'application/ld+json')
echo "JSON-LD script blocks: $COUNT (should be 3: SoftwareApplication + Organization + FAQ)"

echo ""
echo "=== VERIFY GA TAGS ==="
echo "Landing:"
curl -s https://sidixlab.com/ | grep -E 'G-04JKCGDEY4' | head -2
echo "App:"
curl -s https://app.sidixlab.com/ | grep -E 'G-EK6L5SJGY3' | head -2

echo ""
echo "=== CSP CHECK (Content-Security-Policy) ==="
curl -sI https://sidixlab.com/ | grep -iE 'content-security|x-frame|strict-transport' | head -5
