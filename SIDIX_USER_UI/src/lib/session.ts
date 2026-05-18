/**
 * session.ts — Sprint J: Conversation Memory
 * Manages session_id lifecycle for persistent multi-turn conversation.
 *
 * Exported functions are re-exported for use by main.ts and other modules.
 * The actual conversation_id is stored in localStorage under 'sidix_conversation_id',
 * which is already handled by main.ts (getCurrentConversationId / setCurrentConversationId).
 * This file provides the stateless session UUID helpers.
 */

const SESSION_KEY = "sidix_session_id";

/** Return existing session ID from localStorage or generate a new one. */
export function getOrCreateSessionId(): string {
  let id: string | null = null;
  try { id = localStorage.getItem(SESSION_KEY); } catch { /* SSR safe */ }
  if (!id) {
    id = crypto.randomUUID();
    try { localStorage.setItem(SESSION_KEY, id); } catch { /* ignore */ }
  }
  return id;
}

/** Reset to a new session (called on "New Chat"). */
export function newSession(): string {
  const id = crypto.randomUUID();
  try { localStorage.setItem(SESSION_KEY, id); } catch { /* ignore */ }
  return id;
}
