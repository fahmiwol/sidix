path = '/opt/sidix/SIDIX_USER_UI/src/main.ts'
with open(path, encoding='utf-8') as f:
    text = f.read()

# 1. Add setActiveMode('holistic') after declaration
old = "let activeMode: ChatMode = 'holistic'; // default per visi 1000 bayangan"
new = "let activeMode: ChatMode = 'holistic'; // default per visi 1000 bayangan\nsetActiveMode('holistic');"
if old in text:
    text = text.replace(old, new)
    print('1. Added setActiveMode call')
else:
    print('1. FAILED')

# 2. Add routing in handleSend after login gate
marker = """  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  appendMessage('user', question);"""

replacement = """  // ── Auto-mode routing: holistic default ───────────────────────────────────
  if (activeMode === 'holistic') {
    sendBtn.disabled = true;
    modeHolisticBtn?.click();
    return;
  }

  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  appendMessage('user', question);"""

if marker in text:
    text = text.replace(marker, replacement)
    print('2. Added handleSend routing')
else:
    print('2. FAILED')

# 3. Add sendBtn.disabled = false in holistic onDone and onError
# Find the onDone block in holistic event listener
on_done_marker = """      onDone: (meta) => {
        clearInterval(elapsedTimer);
        addProgressLine(
          `Done: confidence=${meta.confidence}, ${meta.nSources} sources, method=${meta.method}, ${(meta.durationMs / 1000).toFixed(1)}s total`,
          'ok',
        );
      },"""

on_done_new = """      onDone: (meta) => {
        clearInterval(elapsedTimer);
        sendBtn.disabled = false;
        addProgressLine(
          `Done: confidence=${meta.confidence}, ${meta.nSources} sources, method=${meta.method}, ${(meta.durationMs / 1000).toFixed(1)}s total`,
          'ok',
        );
      },"""

if on_done_marker in text:
    text = text.replace(on_done_marker, on_done_new)
    print('3a. Added sendBtn enable in onDone')
else:
    print('3a. FAILED')

on_error_marker = """      onError: (msg) => {
        clearInterval(elapsedTimer);
        addProgressLine(`Error: ${msg}`, 'fail');
      },"""

on_error_new = """      onError: (msg) => {
        clearInterval(elapsedTimer);
        sendBtn.disabled = false;
        addProgressLine(`Error: ${msg}`, 'fail');
      },"""

if on_error_marker in text:
    text = text.replace(on_error_marker, on_error_new)
    print('3b. Added sendBtn enable in onError')
else:
    print('3b. FAILED')

# 4. Also add sendBtn.disabled = false in catch block
catch_marker = """  } catch (e) {
    clearInterval(elapsedTimer);
    addProgressLine(`Exception: ${(e as Error).message}`, 'fail');
  }
});"""

catch_new = """  } catch (e) {
    clearInterval(elapsedTimer);
    sendBtn.disabled = false;
    addProgressLine(`Exception: ${(e as Error).message}`, 'fail');
  }
});"""

if catch_marker in text:
    text = text.replace(catch_marker, catch_new)
    print('3c. Added sendBtn enable in catch')
else:
    print('3c. FAILED')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Done.')
