import re

with open('vps_main.ts', encoding='utf-8') as f:
    text = f.read()

# 1. Add setActiveMode('holistic') after declaration
old_decl = "let activeMode: ChatMode = 'holistic'; // default per visi 1000 bayangan"
new_decl = "let activeMode: ChatMode = 'holistic'; // default per visi 1000 bayangan\nsetActiveMode('holistic');"
if old_decl in text:
    text = text.replace(old_decl, new_decl)
    print('1. Added setActiveMode call')
else:
    print('1. DECLARATION NOT FOUND')

# 2. Extract holistic body and create doHolistic function
# Find the event listener block
listener_start = text.find("modeHolisticBtn?.addEventListener('click', async () => {")
if listener_start == -1:
    print('2. LISTENER NOT FOUND')
    exit(1)

# Find the opening brace after async () =>
brace_start = text.find('{', listener_start)
# Find matching closing brace (line 1387)
# We know it ends at the line with "});" after the catch block
# Let's find by pattern: the closing of catch + });
listener_end_pattern = "  } catch (e) {\n    clearInterval(elapsedTimer);\n    addProgressLine(`Exception: ${(e as Error).message}`, 'fail');\n  }\n});"
listener_end = text.find(listener_end_pattern)
if listener_end == -1:
    print('2. LISTENER END NOT FOUND')
    exit(1)
listener_end += len(listener_end_pattern)

full_listener_block = text[listener_start:listener_end]

# Extract body (after opening brace, before closing });
body_start = text.find('{', listener_start) + 1
body_end = listener_end - len("\n});")
body = text[body_start:body_end]

# Remove the first 3 lines: const question = getInputOrPrompt(...); if (!question) return; appendMessage(...); chatInput clear
lines = body.split('\n')
# Find first non-empty line after opening
idx = 0
while idx < len(lines) and lines[idx].strip() == '':
    idx += 1

# Remove lines up to and including chatInput clear
# We expect: const question = getInputOrPrompt(...) | if (!question) return; | appendMessage(...) | if (chatInput) { ... }
new_lines = []
skip_done = False
for line in lines:
    if skip_done:
        new_lines.append(line)
        continue
    stripped = line.strip()
    if stripped.startswith('const question = getInputOrPrompt'):
        continue
    if stripped == "if (!question) return;":
        continue
    if stripped.startswith("appendMessage('user', question)"):
        continue
    if stripped.startswith("if (chatInput) { chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }"):
        skip_done = True
        continue
    if stripped.startswith('if (chatInput)') and "chatInput.value = ''" in stripped:
        skip_done = True
        continue
    new_lines.append(line)

holistic_body = '\n'.join(new_lines)

# Create doHolistic function
do_holistic_fn = f"""
// Extracted from modeHolisticBtn event listener for reuse by handleSend
async function doHolistic(question: string) {{
{holistic_body}
}}
"""

# Replace the full listener block with: doHolistic function + thin event listener wrapper
new_listener = f"""{do_holistic_fn}
modeHolisticBtn?.addEventListener('click', async () => {{
  const question = getInputOrPrompt(
    '🌟 Jurus Seribu Bayangan (Holistic)',
    'Mengerahkan SEMUA resource paralel: web search + knowledge base + semantic embedding + 5 persona research + tools simultan. Sanad cross-verify multi-source. Cognitive synthesizer (neutral) merge jadi 1 jawaban with attribution. Multi-perspective default.',
  );
  if (!question) return;

  appendMessage('user', question);
  if (chatInput) {{ chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }}
  await doHolistic(question);
}});"""

text = text[:listener_start] + new_listener + text[listener_end:]
print('2. Extracted doHolistic function')

# 3. Add branching in handleSend
# Find: appendMessage('user', question); inside handleSend
# We need to add after the appendMessage in handleSend, not the one in event listener
# Search for pattern inside handleSend function
handle_send_marker = """  appendMessage('user', question);

  // Thinking indicator"""
if handle_send_marker in text:
    new_marker = """  appendMessage('user', question);

  // ── Auto-mode routing: holistic default ───────────────────────────────────
  if (activeMode === 'holistic') {
    await doHolistic(question);
    sendBtn.disabled = false;
    return;
  }

  // Thinking indicator"""
    text = text.replace(handle_send_marker, new_marker)
    print('3. Added handleSend routing')
else:
    print('3. HANDLE SEND MARKER NOT FOUND')

with open('vps_main.ts', 'w', encoding='utf-8') as f:
    f.write(text)

print('Done.')
