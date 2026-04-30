# 11 — BUSINESS LOGIC & REACTION FLOW

## State Machines · Decision Trees · Reaction Patterns

**Version:** 1.0 **Date:** 2026-04-25 **Classification:** CORE LOGIC
SPECIFICATION

------------------------------------------------------------------------

## 1. USER STATE MACHINE

### 1.1 Session States

`[ANONYMOUS] ──login──▶ [AUTHENTICATED]`\
`                              │`\
`                              ├──select_client──▶ [IN_BRANCH]`\
`                              │                       │`\
`                              │                       ├──start_chat──▶ [CHATTING]`\
`                              │                       │                  │`\
`                              │                       │                  ├──send_message──▶ [WAITING_RESPONSE]`\
`                              │                       │                  │                      │`\
`                              │                       │                  │                      ├──receive_response──▶ [REVIEWING]`\
`                              │                       │                  │                      │                         │`\
`                              │                       │                  │                      │                         ├──thumbs_up──▶ [SATISFIED]`\
`                              │                       │                  │                      │                         ├──thumbs_down──▶ [DISSATISFIED]`\
`                              │                       │                  │                      │                         └──continue_chat──▶ [CHATTING]`\
`                              │                       │                  │                      │`\
`                              │                       │                  │                      └──timeout──▶ [CHATTING] (retry)`\
`                              │                       │                  │`\
`                              │                       │                  ├──open_tool──▶ [USING_TOOL]`\
`                              │                       │                  │                 │`\
`                              │                       │                  │                 ├──image_editor──▶ [EDITING_IMAGE]`\
`                              │                       │                  │                 ├──video_editor──▶ [EDITING_VIDEO]`\
`                              │                       │                  │                 ├──voice_studio──▶ [RECORDING_AUDIO]`\
`                              │                       │                  │                 └──brand_guidelines──▶ [EDITING_BRAND]`\
`                              │                       │                  │`\
`                              │                       │                  └──start_campaign──▶ [CREATING_CAMPAIGN]`\
`                              │                       │                                      │`\
`                              │                       │                                      ├──brief_entered──▶ [RAUDAH_PLANNING]`\
`                              │                       │                                      │                      │`\
`                              │                       │                                      │                      └──agents_assigned──▶ [AGENTS_WORKING]`\
`                              │                       │                                      │                                             │`\
`                              │                       │                                      │                                             ├──generation_complete──▶ [REVIEWING_DELIVERABLES]`\
`                              │                       │                                      │                                             │                            │`\
`                              │                       │                                      │                                             │                            ├──approve──▶ [SCHEDULING]`\
`                              │                       │                                      │                                             │                            │                │`\
`                              │                       │                                      │                                             │                            │                └──scheduled──▶ [CAMPAIGN_ACTIVE]`\
`                              │                       │                                      │                                             │                            │`\
`                              │                       │                                      │                                             │                            └──request_revision──▶ [AGENTS_WORKING]`\
`                              │                       │                                      │`\
`                              │                       │                                      └──cancel──▶ [CHATTING]`\
`                              │                       │`\
`                              │                       └──switch_client──▶ [IN_BRANCH] (new client)`\
`                              │`\
`                              └──logout──▶ [ANONYMOUS]`

### 1.2 Branch (Client) Context Switching

`class`` BranchContextManager:`\
`    ``"""`\
`    When user switches client:`\
`    1. Save current context to Redis`\
`    2. Load new client context from PostgreSQL + Neo4j`\
`    3. Update system prompt with new brand KG`\
`    4. Switch asset library`\
`    5. Update UI with client-specific data`\
`    """`\
`    `\
`    ``async`` ``def`` switch_branch(``self``, user_id: ``str``, new_client_id: ``str``):`\
`        ``# 1. Save current`\
`        old_client_id ``=`` ``self``.active_branches.get(user_id)`\
`        ``if`` old_client_id:`\
`            ``await`` ``self``._save_context(user_id, old_client_id)`\
`        `\
`        ``# 2. Load new`\
`        client ``=`` ``await`` ``self``._load_client(new_client_id)`\
`        brand_kg ``=`` ``await`` ``self``._load_brand_kg(new_client_id)`\
`        `\
`        ``# 3. Update context`\
`        ``self``.active_branches[user_id] ``=`` new_client_id`\
`        `\
`        ``# 4. Build system prompt`\
`        system_prompt ``=`` ``self``._build_branch_prompt(client, brand_kg)`\
`        `\
`        ``# 5. Notify frontend`\
`        ``await`` ``self``._notify_client_switch(user_id, client)`\
`        `\
`        ``return`` system_prompt`

------------------------------------------------------------------------

## 2. CONVERSATION REACTION FLOW

### 2.1 Query Classification Decision Tree

`INPUT: User Query`\
`│`\
`├─ Is it a greeting? ("halo", "hi", "assalamualaikum")`\
`│  └─ YES → Return greeting + offer help`\
`│`\
`├─ Is it a farewell? ("dadah", "bye", "thank you")`\
`│  └─ YES → Return farewell + summarize session`\
`│`\
`├─ Is it a creative request?`\
`│  ├─ Contains: "buatkan gambar", "generate image", "design logo"`\
`│  │  └─ YES → Route to UTZ (Visual) + Image Editor`\
`│  │`\
`│  ├─ Contains: "buatkan video", "generate video", "edit video"`\
`│  │  └─ YES → Route to UTZ + Video Editor`\
`│  │`\
`│  ├─ Contains: "buatkan copy", "write caption", "script"`\
`│  │  └─ YES → Route to ALEY (Copywriter)`\
`│  │`\
`│  └─ Contains: "buatkan campaign", "brand strategy"`\
`│     └─ YES → Route to AYMAN + Raudah Protocol`\
`│`\
`├─ Is it a code request?`\
`│  ├─ Contains: "code", "script", "function", "API", "build app"`\
`│  │  └─ YES → Route to ALEY + Code Sandbox`\
`│  │`\
`│  └─ Contains: "debug", "fix error", "review code"`\
`│     └─ YES → Route to ABOO + Code Analyze`\
`│`\
`├─ Is it a research/analytics request?`\
`│  ├─ Contains: "analisis", "analyze", "research", "tren", "trend"`\
`│  │  └─ YES → Route to ABOO + Web Search + Analytics`\
`│  │`\
`│  ├─ Contains: "competitor", "market", "benchmark"`\
`│  │  └─ YES → Route to ABOO + Competitor Tracker`\
`│  │`\
`│  └─ Contains: "report", "dashboard", "metrics"`\
`│     └─ YES → Route to ABOO + Report Generator`\
`│`\
`├─ Is it an agency request?`\
`│  ├─ Contains: "client", "campaign", "calendar", "schedule"`\
`│  │  └─ YES → Route to Agency OS module`\
`│  │`\
`│  └─ Contains: "brand guidelines", "logo", "color"`\
`│     └─ YES → Route to Brand Guidelines tool`\
`│`\
`├─ Is it a system request?`\
`│  ├─ Contains: "status", "health", "system"`\
`│  │  └─ YES → Route to Qalb + Health Monitor`\
`│  │`\
`│  ├─ Contains: "train", "learning", "update model"`\
`│  │  └─ YES → Route to Hikmah + Training Pipeline`\
`│  │`\
`│  └─ Contains: "persona", "mode", "settings"`\
`│     └─ YES → Route to Config + Persona Router`\
`│`\
`└─ Default → Route to ALEY (General) + Chat Mode`

### 2.2 Reaction to User Feedback

`class`` FeedbackReactor:`\
`    ``"""`\
`    When user gives feedback, react accordingly:`\
`    """`\
`    `\
`    ``async`` ``def`` on_thumbs_up(``self``, message_id: ``str``):`\
`        ``"""`\
`        1. Mark message as positive in database`\
`        2. Extract high-quality pair for training`\
`        3. Update Knowledge Graph with positive signal`\
`        4. Increase confidence for similar queries`\
`        5. Log to analytics`\
`        """`\
`        ``await`` ``self``.db.messages.update(message_id, {``"feedback"``: ``"positive"``})`\
`        pair ``=`` ``await`` ``self``._extract_training_pair(message_id)`\
`        ``await`` ``self``.aql.capture(pair, quality``=``"high"``)`\
`        ``await`` ``self``.kg.add_positive_signal(pair[``"topic"``])`\
`    `\
`    ``async`` ``def`` on_thumbs_down(``self``, message_id: ``str``, reason: ``str`` ``=`` ``None``):`\
`        ``"""`\
`        1. Mark message as negative`\
`        2. Analyze what went wrong:`\
`           - Wrong answer? → Extract and flag`\
`           - Wrong tone? → Adjust persona weights`\
`           - Wrong format? → Update formatter`\
`           - Cultural issue? → Escalate to Maqashid review`\
`        3. If reason provided, store for analysis`\
`        4. Offer to regenerate with different approach`\
`        """`\
`        ``await`` ``self``.db.messages.update(message_id, {`\
`            ``"feedback"``: ``"negative"``,`\
`            ``"feedback_reason"``: reason`\
`        })`\
`        `\
`        ``if`` reason:`\
`            ``await`` ``self``._categorize_failure(message_id, reason)`\
`        `\
`        ``# Offer regeneration`\
`        ``return`` {`\
`            ``"message"``: ``"Maaf jawaban kurang memuaskan. Apakah ingin saya coba dengan pendekatan berbeda?"``,`\
`            ``"actions"``: [``"Regenerate dengan persona lain"``, ``"Jelaskan masalah lebih detail"``, ``"Lewati"``]`\
`        }`\
`    `\
`    ``async`` ``def`` on_correction(``self``, message_id: ``str``, correct_answer: ``str``):`\
`        ``"""`\
`        1. Store correction as high-quality training pair`\
`        2. Mark original as superseded (Naskh: new > old)`\
`        3. Update Knowledge Graph`\
`        4. Thank user for teaching`\
`        """`\
`        ``await`` ``self``.db.messages.update(message_id, {`\
`            ``"feedback"``: ``"corrected"``,`\
`            ``"correction"``: correct_answer`\
`        })`\
`        `\
`        pair ``=`` ``await`` ``self``._extract_correction_pair(message_id, correct_answer)`\
`        ``await`` ``self``.aql.capture(pair, quality``=``"excellent"``)`\
`        ``await`` ``self``.kg.update_fact(message_id, correct_answer)`\
`        `\
`        ``return`` {``"message"``: ``"Terima kasih atas koreksinya. SIDIX belajar dari ini."``}`

------------------------------------------------------------------------

## 3. CAMPAIGN STATE MACHINE

### 3.1 Campaign Lifecycle

`[DRAFT]`\
`│`\
`├─ User enters brief`\
`│  └─ Auto-save to database`\
`│`\
`├─ User clicks "Generate Campaign"`\
`│  └─ Transition to [PLANNING]`\
`│`\
`[PLANNING]`\
`│`\
`├─ AYMAN generates creative concept`\
`├─ ABOO generates market research`\
`├─ OOMAR generates timeline + budget`\
`│`\
`├─ All agents complete`\
`│  └─ Transition to [CONCEPT_REVIEW]`\
`│`\
`[CONCEPT_REVIEW]`\
`│`\
`├─ User reviews concept`\
`│  ├─ Approves → Transition to [PRODUCTION]`\
`│  ├─ Requests revision → Back to [PLANNING]`\
`│  └─ Rejects → Transition to [DRAFT] (reset)`\
`│`\
`[PRODUCTION]`\
`│`\
`├─ UTZ generates visual assets`\
`├─ ALEY generates copy`\
`├─ All assets generated`\
`│  └─ Transition to [ASSET_REVIEW]`\
`│`\
`[ASSET_REVIEW]`\
`│`\
`├─ User reviews each asset`\
`│  ├─ Approves all → Transition to [SCHEDULING]`\
`│  ├─ Requests revision on some → Back to [PRODUCTION]`\
`│  └─ Rejects concept → Back to [CONCEPT_REVIEW]`\
`│`\
`[SCHEDULING]`\
`│`\
`├─ Content Calendar populated`\
`├─ Auto-best-time calculated`\
`│`\
`├─ User approves schedule`\
`│  └─ Transition to [APPROVED]`\
`│`\
`[APPROVED]`\
`│`\
`├─ Assets finalized`\
`├─ Ready for publish`\
`│`\
`├─ User clicks "Launch Campaign"`\
`│  └─ Transition to [ACTIVE]`\
`│`\
`[ACTIVE]`\
`│`\
`├─ Posts auto-publish (or manual)`\
`├─ Analytics collected`\
`│`\
`├─ Campaign end date reached`\
`│  └─ Transition to [COMPLETED]`\
`│`\
`[COMPLETED]`\
`│`\
`├─ Final report generated`\
`├─ Lessons learned extracted`\
`├─ Archive to project memory`\
`│`\
`└─ User can duplicate → [DRAFT] (clone)`

------------------------------------------------------------------------

## 4. ASSET APPROVAL WORKFLOW

### 4.1 Approval States

`[DRAFT] ──agent completes──▶ [REVIEW]`\
`                                    │`\
`                                    ├─creator_approves──▶ [PENDING_APPROVAL]`\
`                                    │                           │`\
`                                    │                           ├─client_approves──▶ [APPROVED]`\
`                                    │                           │`\
`                                    │                           ├─client_rejects──▶ [REVISION]`\
`                                    │                           │                    │`\
`                                    │                           │                    └─revision_complete──▶ [REVIEW]`\
`                                    │                           │`\
`                                    │                           └─timeout_7days──▶ [AUTO_APPROVED]`\
`                                    │`\
`                                    └─creator_rejects──▶ [DISCARDED]`

### 4.2 Approval Rules

| Role | Can Approve | Can Reject | Can Request Revision |
|:---|:---|:---|:---|
| **Creator** (AI agent) | Auto-approve if CQF \>= 8.0 | If CQF \< 6.0 | If 6.0 \<= CQF \< 8.0 |
| **Team Lead** (human) | All | All | All |
| **Client** (external) | Assets for their brand | Assets for their brand | Assets for their brand |
| **Admin** | All | All | All |

------------------------------------------------------------------------

## 5. ERROR HANDLING & RECOVERY

### 5.1 Error Classification

| Code | Type | Example | Recovery |
|:---|:---|:---|:---|
| E001 | LLM Timeout | Ollama didn’t respond in 30s | Retry with shorter context |
| E002 | LLM Error | Ollama returned 500 | Switch to backup model |
| E003 | Tool Failure | Image generation failed | Retry with different params |
| E004 | DB Error | PostgreSQL connection lost | Reconnect + retry |
| E005 | Rate Limit | Too many requests | Queue + notify user |
| E006 | Validation | Invalid user input | Explain error + ask correction |
| E007 | Maqashid | Output violated filter | Block + explain why |
| E008 | Security | Suspicious input detected | Block + log + alert |
| E009 | Resource | GPU OOM | Switch to CPU + notify |
| E010 | External | Web search API down | Use cached results |

### 5.2 Recovery Logic

`class`` ErrorRecovery:`\
`    MAX_RETRIES ``=`` ``3`\
`    `\
`    ``async`` ``def`` handle(``self``, error: ``Exception``, context: ``dict``) ``->`` ``dict``:`\
`        error_code ``=`` ``self``._classify(error)`\
`        `\
`        ``for`` attempt ``in`` ``range``(``self``.MAX_RETRIES):`\
`            ``try``:`\
`                ``if`` error_code ``==`` ``"E001"``:  ``# Timeout`\
`                    ``# Retry with shorter context`\
`                    context[``"max_tokens"``] ``=`` context.get(``"max_tokens"``, ``2048``) ``//`` ``2`\
`                    ``return`` ``await`` ``self``._retry(context)`\
`                `\
`                ``elif`` error_code ``==`` ``"E002"``:  ``# LLM Error`\
`                    ``# Switch to backup model`\
`                    context[``"model"``] ``=`` ``self``._get_backup_model()`\
`                    ``return`` ``await`` ``self``._retry(context)`\
`                `\
`                ``elif`` error_code ``==`` ``"E003"``:  ``# Tool Failure`\
`                    ``# Retry with different parameters`\
`                    context[``"tool_params"``] ``=`` ``self``._adjust_params(context)`\
`                    ``return`` ``await`` ``self``._retry(context)`\
`                `\
`                ``elif`` error_code ``==`` ``"E004"``:  ``# DB Error`\
`                    ``# Reconnect and retry`\
`                    ``await`` ``self``.db.reconnect()`\
`                    ``return`` ``await`` ``self``._retry(context)`\
`                `\
`                ``elif`` error_code ``==`` ``"E007"``:  ``# Maqashid`\
`                    ``# Cannot recover — block and explain`\
`                    ``return`` {`\
`                        ``"error"``: ``True``,`\
`                        ``"message"``: ``"Mohon maaf, permintaan ini tidak dapat diproses sesuai dengan prinsip Maqashid."`\
`                    }`\
`                `\
`                ``else``:`\
`                    ``# Generic retry`\
`                    ``return`` ``await`` ``self``._retry(context)`\
`                    `\
`            ``except`` ``Exception`` ``as`` e:`\
`                ``if`` attempt ``==`` ``self``.MAX_RETRIES ``-`` ``1``:`\
`                    ``# All retries failed`\
`                    ``return`` ``self``._fallback_response(error_code)`\
`                `\
`                ``await`` asyncio.sleep(``2`` ``**`` attempt)  ``# Exponential backoff`

------------------------------------------------------------------------

## 6. NOTIFICATION LOGIC

### 6.1 When to Notify

| Event                      | Who           | Channel             | Priority |
|:---------------------------|:--------------|:--------------------|:---------|
| Campaign ready for review  | Client + Team | Email + In-app      | High     |
| Asset approved             | Creator       | In-app              | Low      |
| Asset rejected             | Creator       | In-app + Email      | Medium   |
| Post scheduled             | Team          | In-app              | Low      |
| Post published             | Client        | Email               | Medium   |
| Post performance spike     | Team          | In-app + Email      | High     |
| System degraded            | Admin         | Email + SMS         | Critical |
| System critical            | Admin         | Email + SMS + Slack | Critical |
| Weekly report ready        | Client        | Email               | Medium   |
| Trend opportunity detected | Team          | In-app              | Medium   |
| Training complete          | Admin         | Email               | Low      |
| Drift detected             | Admin         | Email               | High     |

### 6.2 Notification Delivery

`class`` NotificationEngine:`\
`    ``async`` ``def`` send(``self``, event: ``str``, recipient: User, data: ``dict``):`\
`        ``# 1. Check user preferences`\
`        prefs ``=`` ``await`` ``self``._get_preferences(recipient)`\
`        `\
`        ``# 2. Route to correct channel`\
`        channels ``=`` []`\
`        ``if`` prefs.email_enabled ``and`` event ``in`` prefs.email_events:`\
`            channels.append(``"email"``)`\
`        ``if`` prefs.push_enabled ``and`` event ``in`` prefs.push_events:`\
`            channels.append(``"push"``)`\
`        ``if`` prefs.sms_enabled ``and`` event ``in`` prefs.sms_events:`\
`            channels.append(``"sms"``)`\
`        `\
`        ``# 3. Always in-app`\
`        channels.append(``"in_app"``)`\
`        `\
`        ``# 4. Send via each channel`\
`        ``for`` channel ``in`` channels:`\
`            ``await`` ``self``._deliver(channel, recipient, event, data)`\
`        `\
`        ``# 5. Store in database`\
`        ``await`` ``self``.db.notifications.create({`\
`            ``"user_id"``: recipient.``id``,`\
`            ``"event"``: event,`\
`            ``"channels"``: channels,`\
`            ``"data"``: data,`\
`            ``"read"``: ``False`\
`        })`

------------------------------------------------------------------------

## 7. RATE LIMITING & FAIR USE

### 7.1 Limits per Tier

| Tier | Image Gen | Video Gen | Code Gen | Chat Messages | Storage |
|:---|:---|:---|:---|:---|:---|
| **Free** (self-hosted) | Unlimited | Unlimited | Unlimited | Unlimited | Unlimited |
| **SIDIX Cloud — Starter** | 100/day | 10/day | 500/day | Unlimited | 10GB |
| **SIDIX Cloud — Pro** | 500/day | 50/day | 2000/day | Unlimited | 50GB |
| **SIDIX Cloud — Agency** | 2000/day | 200/day | Unlimited | Unlimited | 200GB |

### 7.2 Rate Limiting Logic

`class`` RateLimiter:`\
`    ``async`` ``def`` check(``self``, user_id: ``str``, action: ``str``) ``->`` ``bool``:`\
`        key ``=`` ``f"rate_limit:``{``user_id``}``:``{``action``}``"`\
`        `\
`        ``# Get current count`\
`        current ``=`` ``await`` redis.incr(key)`\
`        `\
`        ``# Set expiry on first increment`\
`        ``if`` current ``==`` ``1``:`\
`            ``await`` redis.expire(key, ``60``)  ``# 1-minute window`\
`        `\
`        ``# Get limit for user's tier`\
`        limit ``=`` ``self``._get_limit(user_id, action)`\
`        `\
`        ``if`` current ``>`` limit:`\
`            ``await`` redis.decr(key)  ``# Don't count blocked requests`\
`            ``return`` ``False`\
`        `\
`        ``return`` ``True`\
`    `\
`    ``def`` _get_limit(``self``, user_id: ``str``, action: ``str``) ``->`` ``int``:`\
`        tier ``=`` ``self``._get_user_tier(user_id)`\
`        limits ``=`` {`\
`            ``"free"``: {``"image"``: ``999999``, ``"video"``: ``999999``, ``"code"``: ``999999``, ``"chat"``: ``999999``},`\
`            ``"starter"``: {``"image"``: ``100``, ``"video"``: ``10``, ``"code"``: ``500``, ``"chat"``: ``999999``},`\
`            ``"pro"``: {``"image"``: ``500``, ``"video"``: ``50``, ``"code"``: ``2000``, ``"chat"``: ``999999``},`\
`            ``"agency"``: {``"image"``: ``2000``, ``"video"``: ``200``, ``"code"``: ``999999``, ``"chat"``: ``999999``}`\
`        }`\
`        ``return`` limits[tier].get(action, ``100``)`

------------------------------------------------------------------------

*Logic is the skeleton. Without it, the system collapses. With it, the
system dances.*
