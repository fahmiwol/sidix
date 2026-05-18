#!/bin/bash
# Test script untuk verifikasi multimodal endpoint di production

echo "=== PYTHON ENV CHECK ==="
cd /opt/sidix/apps/brain_qa
python3 - <<'PYEOF'
import os, sys
sys.path.insert(0, '.')
print('GROQ_API_KEY:', 'SET' if os.getenv('GROQ_API_KEY') else 'EMPTY')
print('GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else 'EMPTY')
print('ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'EMPTY')
try:
    import groq
    print('groq SDK:', groq.__version__)
except Exception as e:
    print('groq SDK error:', e)
try:
    from google import genai
    print('google.genai: OK')
except Exception as e:
    print('google.genai:', e)
try:
    import google.generativeai
    print('google.generativeai: OK')
except Exception as e:
    print('google.generativeai:', e)
PYEOF

echo ""
echo "=== TEST TTS (gTTS) ==="
curl -s -X POST "http://localhost:8765/sidix/audio/speak?text=Halo%20saya%20SIDIX&language=id" --max-time 30 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok:',d.get('ok'),'| mode:',d.get('mode'),'| size:',d.get('size_bytes'),'bytes |',d.get('elapsed_ms'),'ms')"

echo ""
echo "=== TEST IMAGE GEN (Pollinations) ==="
curl -s -X POST "http://localhost:8765/sidix/image/generate?prompt=peaceful%20library&size=512x512" --max-time 60 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok:',d.get('ok'),'| mode:',d.get('mode'),'| elapsed:',d.get('elapsed_ms'),'ms')"

echo ""
echo "=== TEST IMAGE ANALYZE (Anthropic vision) ==="
curl -s -X POST "http://localhost:8765/sidix/image/analyze?image_url=https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg&prompt=Apa%20yang%20kamu%20lihat" --max-time 60 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok:',d.get('ok'),'| mode:',d.get('mode'),'| elapsed:',d.get('elapsed_ms'),'ms'); print(d.get('text','')[:300])"

echo ""
echo "=== TEST SKILL MODE fullstack_dev ==="
curl -s -X POST "http://localhost:8765/sidix/mode/fullstack_dev?prompt=cara%20cepat%20bikin%20REST%20API%20Python%20dengan%20auth%20JWT" --max-time 60 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok:',d.get('ok'),'| provider:',d.get('provider'),'| elapsed:',d.get('elapsed_ms'),'ms'); print(d.get('answer','')[:400])"

echo ""
echo "=== TEST DECIDE ==="
curl -s -X POST "http://localhost:8765/sidix/decide?question=Framework%20backend%20yang%20paling%20tepat%20untuk%20startup%20solo%20founder&options_csv=FastAPI%20Python%7CNestJS%20TypeScript%7CGo%20Fiber&voters=3" --max-time 120 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('winner:',d.get('winner'),'confidence:',d.get('confidence'),'text:',d.get('winner_text'))"
