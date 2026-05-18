@echo off
type c:\SIDIX-AI\vps_main.ts.b64 | ssh sidix-vps "python3 -c \"import base64,sys; data=base64.b64decode(sys.stdin.read()); open('/opt/sidix/SIDIX_USER_UI/src/main.ts','wb').write(data)\""
