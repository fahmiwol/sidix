-- SIDIX Agency OS — Core PostgreSQL Schema (Sprint 8a)
-- Source of truth: "02_ERD.md" + "12_INPUT_OUTPUT.md" in sprint-plan complete pack.
-- Notes:
-- - This file is a schema blueprint (apply via your migration tool of choice).
-- - Avoid storing PII in logs/training by default; redact/opt-in where applicable.

-- Required extension for UUIDs
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── Branch system (Agency → Clients) ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS agencies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) NOT NULL,
  industry VARCHAR(100),
  website VARCHAR(255),
  description TEXT,
  status VARCHAR(50) DEFAULT 'active',
  brand_colors JSONB DEFAULT '[]',
  brand_fonts JSONB DEFAULT '[]',
  brand_voice TEXT,
  brand_logo_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(agency_id, slug)
);

-- ── Conversations + Messages + Feedback loop ───────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID REFERENCES agencies(id) ON DELETE SET NULL,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  title VARCHAR(255),
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role VARCHAR(50) NOT NULL, -- user | assistant | system | tool
  content TEXT NOT NULL,
  epistemic_labels JSONB DEFAULT '[]',
  cqf_score DECIMAL(3,1),
  persona_used VARCHAR(50),
  knowledge_layers_used JSONB DEFAULT '[]',
  tool_calls JSONB DEFAULT '[]',
  asset_ids JSONB DEFAULT '[]',
  user_feedback VARCHAR(50) DEFAULT 'none', -- thumbs_up | thumbs_down | none
  feedback_reason TEXT,
  correction TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Jariyah learning: training pairs ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS training_pairs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_query TEXT NOT NULL,
  original_response TEXT NOT NULL,
  corrected_response TEXT,
  source_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
  source_type VARCHAR(50) NOT NULL, -- user_feedback | web_crawl | manual | system
  category VARCHAR(100),
  cqf_score DECIMAL(3,1),
  maqashid_pass BOOLEAN DEFAULT true,
  status VARCHAR(50) DEFAULT 'pending_review',
  review_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Knowledge Graph (per-branch, optional global) ──────────────────────────
CREATE TABLE IF NOT EXISTS kg_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID REFERENCES agencies(id) ON DELETE SET NULL,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  node_type VARCHAR(100) NOT NULL,
  label VARCHAR(255) NOT NULL,
  properties JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kg_relationships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID REFERENCES agencies(id) ON DELETE SET NULL,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  from_node_id UUID REFERENCES kg_nodes(id) ON DELETE CASCADE,
  to_node_id UUID REFERENCES kg_nodes(id) ON DELETE CASCADE,
  relation_type VARCHAR(100) NOT NULL,
  properties JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Observability ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_checks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service_name VARCHAR(100) NOT NULL,
  status VARCHAR(50) NOT NULL, -- ok | warn | error
  details JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_type VARCHAR(50) DEFAULT 'system',
  actor_id VARCHAR(100) DEFAULT '',
  action VARCHAR(100) NOT NULL,
  target_type VARCHAR(100) DEFAULT '',
  target_id VARCHAR(100) DEFAULT '',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

