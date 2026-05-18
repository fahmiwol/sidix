# 12 — INPUT/OUTPUT SPECIFICATIONS

## API Contracts · Data Formats · Message Schemas

**Version:** 1.0 **Date:** 2026-04-25 **Classification:** TECHNICAL
CONTRACT

------------------------------------------------------------------------

## 1. API RESPONSE FORMAT

### 1.1 Standard Response Wrapper

`# Every API response follows this structure:`\
`{`\
`    ``"success"``: ``bool``,                ``# true | false`\
`    ``"data"``: ``any``,                    ``# Payload (varies by endpoint)`\
`    ``"error"``: {                       ``# Present only if success = false`\
`        ``"code"``: ``str``,               ``# Error code (e.g., "E001")`\
`        ``"message"``: ``str``,            ``# Human-readable message`\
`        ``"details"``: ``dict``            ``# Additional context`\
`    },`\
`    ``"meta"``: {                       ``# Metadata`\
`        ``"request_id"``: ``str``,         ``# Unique request ID for tracing`\
`        ``"timestamp"``: ``str``,          ``# ISO 8601 timestamp`\
`        ``"duration_ms"``: ``int``         ``# Response time`\
`    }`\
`}`

### 1.2 Paginated Response

`# For list endpoints:`\
`{`\
`    ``"success"``: true,`\
`    ``"data"``: {`\
`        ``"items"``: [``list``],            ``# Array of results`\
`        ``"pagination"``: {`\
`            ``"page"``: ``int``,            ``# Current page (1-based)`\
`            ``"per_page"``: ``int``,        ``# Items per page`\
`            ``"total"``: ``int``,           ``# Total items`\
`            ``"total_pages"``: ``int``,     ``# Total pages`\
`            ``"has_next"``: ``bool``,       ``# Is there a next page?`\
`            ``"has_prev"``: ``bool``        ``# Is there a previous page?`\
`        }`\
`    },`\
`    ``"meta"``: { ... }`\
`}`

------------------------------------------------------------------------

## 2. AUTHENTICATION I/O

### 2.1 Login

**Request:**

`POST /api/v1/auth/login`\
`Content-Type: application/json`\
\
`{`\
`    "email": "user@example.com",`\
`    "password": "secure_password"`\
`}`

**Success Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"access_token"``:`` ``"eyJhbGciOiJIUzI1NiIs..."``,`\
`        ``"refresh_token"``:`` ``"eyJhbGciOiJIUzI1NiIs..."``,`\
`        ``"token_type"``:`` ``"Bearer"``,`\
`        ``"expires_in"``:`` ``3600``,`\
`        ``"user"``:`` ``{`\
`            ``"id"``:`` ``"uuid"``,`\
`            ``"email"``:`` ``"user@example.com"``,`\
`            ``"full_name"``:`` ``"User Name"``,`\
`            ``"role"``:`` ``"admin"``,`\
`            ``"persona_default"``:`` ``"AYMAN"`\
`        ``}`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

**Error Response:**

`{`\
`    ``"success"``:`` ``false``,`\
`    ``"error"``:`` ``{`\
`        ``"code"``:`` ``"AUTH001"``,`\
`        ``"message"``:`` ``"Email atau password salah"``,`\
`        ``"details"``:`` ``{``"field"``:`` ``"password"``}`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

### 2.2 Authenticated Request Header

`GET /api/v1/clients`\
`Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`\
`X-Client-ID: kai                    # Required in agency mode`

------------------------------------------------------------------------

## 3. CHAT I/O

### 3.1 Send Message

**Request:**

`POST /api/v1/conversations/{id}/messages`\
`Content-Type: application/json`\
`Authorization: Bearer ...`\
\
`{`\
`    "content": "Buatkan campaign Ramadan untuk KAI",`\
`    "persona": "AYMAN",             # Optional: override auto-selection`\
`    "maqashid_mode": "CREATIVE",      # Optional`\
`    "attachments": [                # Optional: images, files`\
`        {"type": "image", "url": "https://..."}`\
`    ]`\
`}`

**Success Response (Sync):**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"message_id"``:`` ``"uuid"``,`\
`        ``"conversation_id"``:`` ``"uuid"``,`\
`        ``"role"``:`` ``"assistant"``,`\
`        ``"content"``:`` ``"Saya akan membuat campaign..."``,`\
`        ``"epistemic_labels"``:`` ``[``"OPINION"``,`` ``"CLAIM"``]``,`\
`        ``"cqf_score"``:`` ``8.5``,`\
`        ``"persona_used"``:`` ``"AYMAN"``,`\
`        ``"knowledge_layers"``:`` ``[``"parametric"``,`` ``"dynamic"``]``,`\
`        ``"tool_calls"``:`` ``[`\
`            ``{``"name"``:`` ``"generate_campaign"``,`` ``"args"``:`` ``{``"client_id"``:`` ``"kai"``}}`\
`        ``]``,`\
`        ``"assets"``:`` ``[``                     ``#`` ``Generated`` ``assets`\
`            ``{`\
`                ``"asset_id"``:`` ``"uuid"``,`\
`                ``"type"``:`` ``"campaign_concept"``,`\
`                ``"preview_url"``:`` ``"https://cdn.../concept.png"``,`\
`                ``"download_url"``:`` ``"https://cdn.../concept.pdf"`\
`            ``}`\
`        ``]``,`\
`        ``"created_at"``:`` ``"2026-04-25T10:30:00Z"`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

**Success Response (Async - WebSocket):**

`//`` ``Chunk`` ``1:`` ``Thinking`\
`{`\
`    ``"type"``:`` ``"chat.stream"``,`\
`    ``"conversation_id"``:`` ``"uuid"``,`\
`    ``"status"``:`` ``"thinking"``,`\
`    ``"agent"``:`` ``"AYMAN"``,`\
`    ``"chunk"``:`` ``"Sedang menganalisis brief..."`\
`}`\
\
`//`` ``Chunk`` ``2:`` ``Tool`` ``call`\
`{`\
`    ``"type"``:`` ``"agent.thought"``,`\
`    ``"agent"``:`` ``"ABOO"``,`\
`    ``"thought"``:`` ``"Trend analysis: skincare Ramadan naik 45%"``,`\
`    ``"tool_calls"``:`` ``[``"search_web"``,`` ``"analyze_trend"``]`\
`}`\
\
`//`` ``Chunk`` ``3:`` ``Content`\
`{`\
`    ``"type"``:`` ``"chat.stream"``,`\
`    ``"conversation_id"``:`` ``"uuid"``,`\
`    ``"status"``:`` ``"generating"``,`\
`    ``"chunk"``:`` ``"Berikut konsep campaign..."`\
`}`\
\
`//`` ``Final:`` ``Complete`\
`{`\
`    ``"type"``:`` ``"chat.complete"``,`\
`    ``"conversation_id"``:`` ``"uuid"``,`\
`    ``"message_id"``:`` ``"uuid"``,`\
`    ``"content"``:`` ``"Full markdown content"``,`\
`    ``"assets"``:`` ``[``...``]``,`\
`    ``"cqf_score"``:`` ``8.5`\
`}`

### 3.2 Conversation Object

`{`\
`    ``"id"``: ``"uuid"``,`\
`    ``"title"``: ``"Campaign KAI Ramadan"``,    ``# Auto-generated from first message`\
`    ``"client_id"``: ``"kai"``,                 ``# Null if not agency mode`\
`    ``"user_id"``: ``"uuid"``,`\
`    ``"active_persona"``: ``"AYMAN"``,`\
`    ``"active_tools"``: [``"image_editor"``, ``"campaign_builder"``],`\
`    ``"mode"``: ``"creative"``,                 ``# chat | creative | analysis | code`\
`    ``"maqashid_mode"``: ``"CREATIVE"``,`\
`    ``"message_count"``: ``15``,`\
`    ``"last_message_at"``: ``"2026-04-25T10:30:00Z"``,`\
`    ``"created_at"``: ``"2026-04-25T09:00:00Z"``,`\
`    ``"messages"``: [                       ``# Embedded (last 50)`\
`        {`\
`            ``"id"``: ``"uuid"``,`\
`            ``"role"``: ``"user"``,             ``# user | assistant | system | tool`\
`            ``"content"``: ``"..."``,`\
`            ``"epistemic_labels"``: [],`\
`            ``"cqf_score"``: null,`\
`            ``"tool_calls"``: [],`\
`            ``"created_at"``: ``"..."`\
`        }`\
`    ]`\
`}`

------------------------------------------------------------------------

## 4. GENERATION I/O

### 4.1 Image Generation

**Request:**

`POST /api/v1/generate/image`\
`Content-Type: application/json`\
\
`{`\
`    "prompt": "professional photography, Indonesian train station, golden hour, warm tones, families gathering for Ramadan homecoming, Kereta Api Indonesia branding visible",`\
`    "negative_prompt": "blurry, low quality, modern cold tones, unrelated people",`\
`    "width": 1080,`\
`    "height": 1080,`\
`    "model": "flux.1-dev",              # Optional: flux.1-schnell | flux.1-dev | sdxl`\
`    "steps": 50,                        # 20-50`\
`    "guidance_scale": 7.5,            # 5.0-10.0`\
`    "seed": 42,                         # Optional: for reproducibility`\
`    "style_preset": "photorealistic",   # Optional`\
`    "client_id": "kai"                  # For brand context`\
`}`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"asset_id"``:`` ``"uuid"``,`\
`        ``"image_url"``:`` ``"https://cdn.sidix/.../image.png"``,`\
`        ``"thumbnail_url"``:`` ``"https://cdn.sidix/.../thumb.png"``,`\
`        ``"width"``:`` ``1080``,`\
`        ``"height"``:`` ``1080``,`\
`        ``"format"``:`` ``"png"``,`\
`        ``"file_size_bytes"``:`` ``2457600``,`\
`        ``"generation_time_ms"``:`` ``8500``,`\
`        ``"cqf_score"``:`` ``8.7``,`\
`        ``"ai_metadata"``:`` ``{`\
`            ``"model"``:`` ``"flux.1-dev"``,`\
`            ``"prompt"``:`` ``"..."``,`\
`            ``"negative_prompt"``:`` ``"..."``,`\
`            ``"steps"``:`` ``50``,`\
`            ``"guidance_scale"``:`` ``7.5``,`\
`            ``"seed"``:`` ``42`\
`        ``},`\
`        ``"variations"``:`` ``[``                 ``#`` ``4`` ``additional`` ``variations`\
`            ``{``"asset_id"``:`` ``"uuid-2"``,`` ``"thumbnail_url"``:`` ``"..."``}``,`\
`            ``{``"asset_id"``:`` ``"uuid-3"``,`` ``"thumbnail_url"``:`` ``"..."``}``,`\
`            ``{``"asset_id"``:`` ``"uuid-4"``,`` ``"thumbnail_url"``:`` ``"..."``}``,`\
`            ``{``"asset_id"``:`` ``"uuid-5"``,`` ``"thumbnail_url"``:`` ``"..."``}`\
`        ``]`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

### 4.2 Video Generation

**Request:**

`POST /api/v1/generate/video`\
`Content-Type: application/json`\
\
`{`\
`    "prompt": "cinematic shot, train moving through Indonesian countryside at sunset, warm golden light, families looking out windows with joy",`\
`    "input_image": "https://cdn.sidix/.../keyframe.png",  # Optional: image-to-video`\
`    "duration": 5,                    # 1-10 seconds`\
`    "fps": 24,`\
`    "resolution": "720p",             # 480p | 720p | 1080p`\
`    "aspect_ratio": "16:9",             # 16:9 | 9:16 | 1:1`\
`    "model": "cogvideox-5b"`\
`}`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"asset_id"``:`` ``"uuid"``,`\
`        ``"video_url"``:`` ``"https://cdn.sidix/.../video.mp4"``,`\
`        ``"thumbnail_url"``:`` ``"https://cdn.sidix/.../thumb.jpg"``,`\
`        ``"preview_gif_url"``:`` ``"https://cdn.sidix/.../preview.gif"``,`\
`        ``"duration"``:`` ``5``,`\
`        ``"width"``:`` ``1280``,`\
`        ``"height"``:`` ``720``,`\
`        ``"fps"``:`` ``24``,`\
`        ``"format"``:`` ``"mp4"``,`\
`        ``"file_size_mb"``:`` ``12.5``,`\
`        ``"generation_time_ms"``:`` ``45000``,`\
`        ``"cqf_score"``:`` ``7.8`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

### 4.3 Code Generation

**Request:**

`POST /api/v1/generate/code`\
`Content-Type: application/json`\
\
`{`\
`    "task": "Create a FastAPI endpoint for user authentication with JWT, including login, register, and refresh token",`\
`    "language": "python",`\
`    "framework": "fastapi",`\
`    "include_tests": true,`\
`    "include_docs": true,`\
`    "style_guide": "pep8"`\
`}`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"project_id"``:`` ``"uuid"``,`\
`        ``"files"``:`` ``{`\
`            ``"auth.py"``:`` ``{`\
`                ``"content"``:`` ``"from fastapi import..."``,`\
`                ``"language"``:`` ``"python"``,`\
`                ``"lines"``:`` ``150`\
`            ``},`\
`            ``"models.py"``:`` ``{`\
`                ``"content"``:`` ``"from pydantic import..."``,`\
`                ``"language"``:`` ``"python"``,`\
`                ``"lines"``:`` ``45`\
`            ``},`\
`            ``"test_auth.py"``:`` ``{`\
`                ``"content"``:`` ``"import pytest..."``,`\
`                ``"language"``:`` ``"python"``,`\
`                ``"lines"``:`` ``80`\
`            ``},`\
`            ``"README.md"``:`` ``{`\
`                ``"content"``:`` ``"# Authentication Module..."``,`\
`                ``"language"``:`` ``"markdown"``,`\
`                ``"lines"``:`` ``30`\
`            ``}`\
`        ``},`\
`        ``"validation"``:`` ``{`\
`            ``"syntax_valid"``:`` ``true``,`\
`            ``"tests_pass"``:`` ``true``,`\
`            ``"security_scan"``:`` ``"passed"``,`\
`            ``"issues"``:`` ``[]`\
`        ``},`\
`        ``"dependencies"``:`` ``[`\
`            ``"fastapi>=0.115.0"``,`\
`            ``"python-jose[cryptography]>=3.3.0"``,`\
`            ``"passlib[bcrypt]>=1.7.4"`\
`        ``]``,`\
`        ``"cqf_score"``:`` ``8.9`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

------------------------------------------------------------------------

## 5. AGENCY OS I/O

### 5.1 Create Client (Branch)

**Request:**

`POST /api/v1/clients`\
`Content-Type: application/json`\
\
`{`\
`    "name": "PT Kereta Api Indonesia",`\
`    "slug": "kai",`\
`    "industry": "transportation",`\
`    "website": "https://kai.id",`\
`    "description": "Indonesian state railway company",`\
`    "contact_name": "Budi Santoso",`\
`    "contact_email": "budi@kai.id",`\
`    "monthly_budget": 50000000,`\
`    "brand_colors": [`\
`        {"name": "Primary", "hex": "#0033A0"},`\
`        {"name": "Accent", "hex": "#FF6600"}`\
`    ],`\
`    "brand_fonts": [`\
`        {"role": "heading", "family": "Montserrat"},`\
`        {"role": "body", "family": "Open Sans"}`\
`    ]`\
`}`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"id"``:`` ``"uuid"``,`\
`        ``"name"``:`` ``"PT Kereta Api Indonesia"``,`\
`        ``"slug"``:`` ``"kai"``,`\
`        ``"status"``:`` ``"active"``,`\
`        ``"brand_guideline_id"``:`` ``"uuid"``,`\
`        ``"created_at"``:`` ``"2026-04-25T10:00:00Z"``,`\
`        ``"setup_complete"``:`` ``false``,``      ``#`` ``Next`` ``step``:`` ``run`` ``brand`` ``extraction`\
`        ``"next_steps"``:`` ``[`\
`            ``"Run brand guideline extraction"``,`\
`            ``"Upload logo files"``,`\
`            ``"Create first campaign"`\
`        ``]`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

### 5.2 Generate Campaign

**Request:**

`POST /api/v1/clients/{client_id}/campaigns`\
`Content-Type: application/json`\
\
`{`\
`    "name": "Ramadan 2026 - Pulang",`\
`    "objective": "brand_awareness",`\
`    "target_audience": "Gen Z and millennials, 18-35, urban Indonesia, Muslim",`\
`    "budget": 50000000,`\
`    "start_date": "2026-03-01",`\
`    "end_date": "2026-04-15",`\
`    "description": "Campaign highlighting the emotional journey of homecoming during Ramadan via KAI",`\
`    "deliverables_requested": {`\
`        "images": 10,`\
`        "videos": 3,`\
`        "copy_posts": 20,`\
`        "stories": 15`\
`    }`\
`}`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"campaign_id"``:`` ``"uuid"``,`\
`        ``"status"``:`` ``"draft"``,`\
`        ``"creative_concept"``:`` ``{`\
`            ``"title"``:`` ``"Perjalanan Pulang"``,`\
`            ``"theme"``:`` ``"Emotional connection between train travel and Ramadan homecoming"``,`\
`            ``"visual_direction"``:`` ``"Warm gold tones, nostalgic photography, family reunion scenes"``,`\
`            ``"messaging_framework"``:`` ``{`\
`                ``"headline"``:`` ``"Setiap Perjalanan, Sebuah Pulang"``,`\
`                ``"tagline"``:`` ``"KAI, Mengantar Anda ke Pelukan Keluarga"``,`\
`                ``"tone"``:`` ``"warm, nostalgic, hopeful"`\
`            ``}`\
`        ``},`\
`        ``"timeline"``:`` ``{`\
`            ``"research"``:`` ``"2026-02-15 to 2026-02-20"``,`\
`            ``"concept"``:`` ``"2026-02-21 to 2026-02-25"``,`\
`            ``"production"``:`` ``"2026-02-26 to 2026-03-05"``,`\
`            ``"review"``:`` ``"2026-03-06 to 2026-03-10"``,`\
`            ``"launch"``:`` ``"2026-03-11"`\
`        ``},`\
`        ``"budget_breakdown"``:`` ``{`\
`            ``"production"``:`` ``25000000``,`\
`            ``"media_spend"``:`` ``20000000``,`\
`            ``"contingency"``:`` ``5000000`\
`        ``},`\
`        ``"agents_assigned"``:`` ``[``"AYMAN"``,`` ``"ABOO"``,`` ``"UTZ"``,`` ``"ALEY"``,`` ``"OOMAR"``]``,`\
`        ``"workflow_status"``:`` ``"pending"``,`\
`        ``"created_at"``:`` ``"2026-04-25T10:00:00Z"`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

### 5.3 Content Calendar Entry

**Request:**

`POST /api/v1/clients/{client_id}/calendar`\
`Content-Type: application/json`\
\
`{`\
`    "platform": "instagram",`\
`    "content_type": "feed",`\
`    "caption": "Setiap perjalanan punya cerita. Apa momen paling berkesan saat pulang kampung? 🚂✨ #KAIRamadan #PulangBerkah",`\
`    "hashtags": ["#KAIRamadan", "#PulangBerkah", "#KeretaApiIndonesia"],`\
`    "asset_ids": ["uuid-1", "uuid-2"],`\
`    "scheduled_at": "2026-03-15T18:00:00+07:00",`\
`    "timezone": "Asia/Jakarta"`\
`}`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"calendar_id"``:`` ``"uuid"``,`\
`        ``"status"``:`` ``"scheduled"``,`\
`        ``"platform"``:`` ``"instagram"``,`\
`        ``"scheduled_at"``:`` ``"2026-03-15T18:00:00+07:00"``,`\
`        ``"best_time_confidence"``:`` ``0``.``92``,``   ``#`` ``AI-calculated`` ``optimal`` ``time`\
`        ``"estimated_reach"``:`` ``45000``,`\
`        ``"estimated_engagement"``:`` ``8.2``,`\
`        ``"approval_status"``:`` ``"pending"``,``     ``#`` ``Needs`` ``team/client`` ``approval`\
`        ``"preview"``:`` ``{`\
`            ``"image_url"``:`` ``"https://cdn.../preview.png"``,`\
`            ``"rendered_caption"``:`` ``"Setiap perjalanan punya cerita..."`\
`        ``}`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

------------------------------------------------------------------------

## 6. WEBSOCKET MESSAGE SCHEMA

### 6.1 Client → Server Messages

`// Chat message`\
`type`` ChatMessage ``=`` {`\
`    type``:`` ``"chat.message"``;`\
`    conversation_id``:`` ``string``;`\
`    content``:`` ``string``;`\
`    persona``?:`` ``"AYMAN"`` ``|`` ``"ABOO"`` ``|`` ``"OOMAR"`` ``|`` ``"UTZ"`` ``|`` ``"ALEY"``;`\
`    client_id``?:`` ``string``;`\
`    attachments``?:`` ``Array``<``{`\
`        type``:`` ``"image"`` ``|`` ``"file"``;`\
`        url``:`` ``string``;`\
`        name``?:`` ``string``;`\
`    }``>;`\
`}``;`\
\
`// Tool action`\
`type`` ToolAction ``=`` {`\
`    type``:`` ``"editor.action"``;`\
`    tool``:`` ``"image_editor"`` ``|`` ``"video_editor"`` ``|`` ``"voice_studio"``;`\
`    action``:`` ``"generate"`` ``|`` ``"edit"`` ``|`` ``"export"``;`\
`    params``:`` ``Record``<``string``,`` ``any``>;`\
`}``;`\
\
`// Feedback`\
`type`` FeedbackMessage ``=`` {`\
`    type``:`` ``"feedback"``;`\
`    message_id``:`` ``string``;`\
`    feedback``:`` ``"thumbs_up"`` ``|`` ``"thumbs_down"`` ``|`` ``"correction"``;`\
`    reason``?:`` ``string``;`\
`    correction``?:`` ``string``;`\
`}``;`\
\
`// Typing indicator`\
`type`` TypingMessage ``=`` {`\
`    type``:`` ``"typing"``;`\
`    conversation_id``:`` ``string``;`\
`    is_typing``:`` ``boolean``;`\
`}``;`

### 6.2 Server → Client Messages

`// Streaming response chunk`\
`type`` StreamChunk ``=`` {`\
`    type``:`` ``"chat.stream"``;`\
`    conversation_id``:`` ``string``;`\
`    message_id``:`` ``string``;`\
`    chunk``:`` ``string``;``                    # ``Text`` chunk`\
`    agent``?:`` ``string``;``                   # Which agent is responding`\
`    status``:`` ``"thinking"`` ``|`` ``"generating"`` ``|`` ``"tool_call"`` ``|`` ``"complete"``;`\
`    tool_calls``?:`` ``Array``<``{`\
`        name``:`` ``string``;`\
`        args``:`` ``Record``<``string``,`` ``any``>;`\
`    }``>;`\
`}``;`\
\
`// Asset generated`\
`type`` AssetGenerated ``=`` {`\
`    type``:`` ``"asset.generated"``;`\
`    asset_id``:`` ``string``;`\
`    asset_type``:`` ``"image"`` ``|`` ``"video"`` ``|`` ``"audio"`` ``|`` ``"document"``;`\
`    preview_url``:`` ``string``;`\
`    download_url``:`` ``string``;`\
`    cqf_score``:`` ``number``;`\
`    generation_time_ms``:`` ``number``;`\
`}``;`\
\
`// Agent thought process (visible to user)`\
`type`` AgentThought ``=`` {`\
`    type``:`` ``"agent.thought"``;`\
`    agent``:`` ``string``;`\
`    thought``:`` ``string``;`\
`    tool_calls``?:`` ``Array``<``{`\
`        name``:`` ``string``;`\
`        status``:`` ``"started"`` ``|`` ``"completed"`` ``|`` ``"failed"``;`\
`    }``>;`\
`}``;`\
\
`// Notification`\
`type`` ``Notification`` ``=`` {`\
`    type``:`` ``"system.notification"``;`\
`    title``:`` ``string``;`\
`    message``:`` ``string``;`\
`    link``?:`` ``string``;`\
`    priority``:`` ``"low"`` ``|`` ``"medium"`` ``|`` ``"high"`` ``|`` ``"critical"``;`\
`}``;`\
\
`// Health update`\
`type`` HealthUpdate ``=`` {`\
`    type``:`` ``"system.health"``;`\
`    component``:`` ``string``;`\
`    status``:`` ``"healthy"`` ``|`` ``"degraded"`` ``|`` ``"sick"`` ``|`` ``"critical"``;`\
`    metrics``:`` ``Record``<``string``,`` ``number``>;`\
`}``;`

------------------------------------------------------------------------

## 7. FILE UPLOAD I/O

### 7.1 Upload Asset

**Request:**

`POST /api/v1/clients/{client_id}/assets/upload`\
`Content-Type: multipart/form-data`\
`Authorization: Bearer ...`\
\
`file: [binary data]`\
`name: "KAI_Logo_2026.png"`\
`type: "image"`\
`tags: "[\"logo\", \"branding\", \"2026\"]"`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"asset_id"``:`` ``"uuid"``,`\
`        ``"name"``:`` ``"KAI_Logo_2026.png"``,`\
`        ``"type"``:`` ``"image"``,`\
`        ``"format"``:`` ``"png"``,`\
`        ``"storage_path"``:`` ``"agencies/default/kai/images/raw/uuid.png"``,`\
`        ``"public_url"``:`` ``"https://cdn.sidix/.../uuid.png"``,`\
`        ``"thumbnail_url"``:`` ``"https://cdn.sidix/.../uuid_thumb.png"``,`\
`        ``"dimensions"``:`` ``"2000x2000"``,`\
`        ``"file_size_bytes"``:`` ``512000``,`\
`        ``"tags"``:`` ``[``"logo"``,`` ``"branding"``,`` ``"2026"``]``,`\
`        ``"uploaded_by"``:`` ``"uuid"``,`\
`        ``"created_at"``:`` ``"2026-04-25T10:00:00Z"`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

------------------------------------------------------------------------

## 8. ANALYTICS I/O

### 8.1 Get Dashboard Data

**Request:**

`GET /api/v1/clients/{client_id}/analytics/dashboard?start_date=2026-04-01&end_date=2026-04-25&platform=all`\
`Authorization: Bearer ...`

**Response:**

`{`\
`    ``"success"``:`` ``true``,`\
`    ``"data"``:`` ``{`\
`        ``"period"``:`` ``{``"start"``:`` ``"2026-04-01"``,`` ``"end"``:`` ``"2026-04-25"``},`\
`        ``"summary"``:`` ``{`\
`            ``"total_posts"``:`` ``45``,`\
`            ``"total_reach"``:`` ``1250000``,`\
`            ``"total_engagement"``:`` ``87500``,`\
`            ``"engagement_rate"``:`` ``7.0``,`\
`            ``"followers_growth"``:`` ``3200``,`\
`            ``"website_clicks"``:`` ``5400``,`\
`            ``"conversions"``:`` ``120`\
`        ``},`\
`        ``"by_platform"``:`` ``{`\
`            ``"instagram"``:`` ``{`\
`                ``"posts"``:`` ``20``,`\
`                ``"reach"``:`` ``600000``,`\
`                ``"engagement_rate"``:`` ``8.2``,`\
`                ``"top_post"``:`` ``{``"asset_id"``:`` ``"uuid"``,`` ``"engagement"``:`` ``15000``}`\
`            ``},`\
`            ``"tiktok"``:`` ``{`\
`                ``"posts"``:`` ``15``,`\
`                ``"reach"``:`` ``500000``,`\
`                ``"engagement_rate"``:`` ``9.5``,`\
`                ``"top_video"``:`` ``{``"asset_id"``:`` ``"uuid"``,`` ``"views"``:`` ``200000``}`\
`            ``},`\
`            ``"twitter"``:`` ``{`\
`                ``"posts"``:`` ``10``,`\
`                ``"reach"``:`` ``150000``,`\
`                ``"engagement_rate"``:`` ``4.1`\
`            ``}`\
`        ``},`\
`        ``"ai_insights"``:`` ``[`\
`            ``"Reels format menunjukkan engagement 45% lebih tinggi dari feed posts"``,`\
`            ``"Best posting time: 18:00-20:00 WIB menghasilkan 30% lebih banyak reach"``,`\
`            ``"Topik 'nostalgia' resonansi tinggi dengan target audience"`\
`        ``]``,`\
`        ``"competitor_benchmark"``:`` ``{`\
`            ``"our_engagement"``:`` ``7.0``,`\
`            ``"industry_avg"``:`` ``5.2``,`\
`            ``"top_competitor"``:`` ``6.8`\
`        ``}`\
`    ``},`\
`    ``"meta"``:`` ``{`` ``...`` ``}`\
`}`

------------------------------------------------------------------------

## 9. ERROR RESPONSE CODES

| Code | HTTP Status | Meaning | User Message (Indonesian) |
|:---|:---|:---|:---|
| AUTH001 | 401 | Invalid credentials | Email atau password salah |
| AUTH002 | 401 | Token expired | Sesi Anda telah berakhir, silakan login ulang |
| AUTH003 | 403 | Insufficient permissions | Anda tidak memiliki akses untuk ini |
| VAL001 | 400 | Invalid input | Input tidak valid, silakan periksa kembali |
| VAL002 | 400 | Missing required field | Field \[X\] wajib diisi |
| GEN001 | 500 | LLM timeout | AI sedang sibuk, silakan coba lagi |
| GEN002 | 500 | Generation failed | Gagal membuat konten, silakan coba dengan deskripsi berbeda |
| GEN003 | 422 | Maqashid violation | Mohon maaf, permintaan ini tidak dapat diproses sesuai prinsip Maqashid |
| RES001 | 429 | Rate limit exceeded | Anda telah mencapai batas harian, coba lagi besok |
| RES002 | 503 | Service unavailable | Sistem sedang maintenance, silakan tunggu |
| RES003 | 500 | Database error | Terjadi kesalahan sistem, tim kami sedang memperbaiki |
| NET001 | 502 | Ollama unreachable | AI model sedang tidak tersedia, silakan coba lagi |
| NET002 | 504 | Gateway timeout | Koneksi lambat, silakan coba lagi |

------------------------------------------------------------------------

## 10. DATA FORMATS

### 10.1 Date/Time

- All dates in **ISO 8601** format: `2026-04-25T10:30:00+07:00`
- Timezone default: `Asia/Jakarta` (+07:00)
- Stored in PostgreSQL as `TIMESTAMP WITH TIME ZONE`

### 10.2 Currency

- Default: **IDR** (Indonesian Rupiah)
- Stored as `DECIMAL(12,2)`
- Display: `Rp 50.000.000` (with periods as thousand separators)

### 10.3 Image Dimensions

- Format: `"{width}x{height}"` e.g., `"1080x1080"`
- Aspect ratio derived from dimensions

### 10.4 File Sizes

- Stored in **bytes**
- Display: Human readable (“2.5 MB”, “150 KB”)

### 10.5 Color Values

- Format: **Hex** with `#` prefix: `"#0033A0"`
- Also stored as RGB: `{"r": 0, "g": 51, "b": 160}`

------------------------------------------------------------------------

*Clear contracts make happy integrations. Every field has a purpose.
Every type has a reason.*
