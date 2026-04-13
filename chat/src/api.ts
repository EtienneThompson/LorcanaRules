import type { CardReference, CardSearchResult, Citation } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

interface StreamCallbacks {
  onText: (text: string) => void;
  onCitation: (citation: Citation) => void;
  onCard: (card: CardReference) => void;
}

/**
 * Search for cards whose name starts with the given prefix.
 * Returns an empty array on error or empty query.
 */
export async function searchCards(
  prefix: string,
  signal?: AbortSignal,
): Promise<CardSearchResult[]> {
  if (!prefix) return [];
  try {
    const response = await fetch(
      `${API_BASE}/search_cards?q=${encodeURIComponent(prefix)}`,
      { signal },
    );
    if (!response.ok) return [];
    return response.json();
  } catch (err) {
    // Suppress abort errors — the caller intentionally cancelled.
    if (err instanceof Error && err.name === 'AbortError') return [];
    return [];
  }
}

/**
 * Call the /chat endpoint and invoke callbacks for each streamed event.
 * Returns when the stream ends.
 */
export async function streamChat(
  query: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const payload = line.slice(6).trim();
      if (payload === '[DONE]') return;
      try {
        const parsed = JSON.parse(payload) as
          | { type: 'text'; text: string }
          | { type: 'citation'; number: number; rule_id: string; rule_text: string }
          | { type: 'card'; card_id: number; full_name: string; image_url: string };

        if (parsed.type === 'text') {
          callbacks.onText(parsed.text);
        } else if (parsed.type === 'citation') {
          callbacks.onCitation({
            number: parsed.number,
            rule_id: parsed.rule_id,
            rule_text: parsed.rule_text,
          });
        } else if (parsed.type === 'card') {
          callbacks.onCard({
            card_id: parsed.card_id,
            full_name: parsed.full_name,
            image_url: parsed.image_url,
          });
        }
      } catch {
        // ignore malformed lines
      }
    }
  }
}
