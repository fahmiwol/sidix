#!/bin/bash
set -e
cd /opt/sidix

echo "=== PULL LATEST ==="
git pull origin main 2>&1 | tail -3

echo ""
echo "=== INSTALL PILLOW (if needed) ==="
python3 -c "from PIL import Image" 2>/dev/null && echo "Pillow OK" || pip3 install Pillow 2>&1 | tail -2

echo ""
echo "=== GENERATE OG-IMAGE ==="
python3 /opt/sidix/apps/brain_qa/scripts/generate_og_image.py
ls -la /www/wwwroot/sidixlab.com/og-image.png 2>&1

echo ""
echo "=== SYNC LANDING (index + privacy) ==="
cp -v /opt/sidix/SIDIX_LANDING/index.html /www/wwwroot/sidixlab.com/index.html
cp -v /opt/sidix/SIDIX_LANDING/privacy.html /www/wwwroot/sidixlab.com/privacy.html

echo ""
echo "=== REBUILD UI ==="
cd /opt/sidix/SIDIX_USER_UI
npm run build 2>&1 | tail -3

echo ""
echo "=== RESTART UI + CLEAR PROXY CACHE ==="
pm2 restart sidix-ui
rm -rf /www/wwwroot/app.sidixlab.com/proxy_cache_dir/* 2>/dev/null && echo "cache cleared" || echo "(no cache dir)"

echo ""
echo "=== VERIFY ==="
echo "OG image:"
curl -sI https://sidixlab.com/og-image.png | head -3
echo ""
echo "GA tag landing:"
curl -s https://sidixlab.com/ | grep -E 'G-04JKCGDEY4|googletagmanager' | head -3
echo ""
echo "GA tag app:"
curl -s https://app.sidixlab.com/ | grep -E 'G-EK6L5SJGY3|googletagmanager' | head -3
