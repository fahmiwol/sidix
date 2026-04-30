path = '/opt/sidix/apps/brain_qa/brain_qa/daily_self_critique.py'
with open(path) as f:
    text = f.read()

text = text.replace('Path(".data/critique")', 'Path("/opt/sidix/.data/critique")')
text = text.replace('Path(".data/sessions")', 'Path("/opt/sidix/.data/sessions")')

with open(path, 'w') as f:
    f.write(text)
print('fixed')
