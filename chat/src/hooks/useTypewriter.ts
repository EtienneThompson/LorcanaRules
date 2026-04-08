import { useEffect, useRef, useState } from 'react';

/** Characters to reveal per tick. */
const CHARS_PER_TICK = 1;
/** Milliseconds between ticks — 15ms gives ~67 chars/sec. */
const TICK_MS = 15;

/** Matches an inline marker embedded in the text, e.g. `cite:3` or `card:42` */
const MARKER_RE = /^`(?:cite|card):\d+`/;

/**
 * Returns a progressively revealed substring of `fullText`, advancing
 * CHARS_PER_TICK characters every TICK_MS milliseconds.
 *
 * Citation markers (`` `cite:N` ``) are always revealed atomically — the
 * display position jumps to the end of the marker in a single tick so a
 * badge never appears half-rendered.
 */
export function useTypewriter(fullText: string, streaming: boolean): string {
  const posRef = useRef(0);
  const fullTextRef = useRef(fullText);
  const streamingRef = useRef(streaming);

  useEffect(() => { fullTextRef.current = fullText; }, [fullText]);
  useEffect(() => { streamingRef.current = streaming; }, [streaming]);

  const [, forceRender] = useState(0);

  useEffect(() => {
    posRef.current = 0;

    const id = setInterval(() => {
      const full = fullTextRef.current;
      const target = full.length;

      if (posRef.current < target) {
        let next = Math.min(posRef.current + CHARS_PER_TICK, target);

        // If the next reveal position lands inside a marker, jump past it.
        const backtickIdx = (() => {
          const c = full.indexOf('`cite:', posRef.current);
          const k = full.indexOf('`card:', posRef.current);
          if (c === -1) return k;
          if (k === -1) return c;
          return Math.min(c, k);
        })();
        if (backtickIdx !== -1 && backtickIdx < next) {
          const markerMatch = full.slice(backtickIdx).match(MARKER_RE);
          if (markerMatch) {
            next = backtickIdx + markerMatch[0].length;
          }
        }
        // Also handle landing exactly at the start of a marker.
        const atMarker = full.slice(next).match(MARKER_RE);
        if (atMarker) {
          next += atMarker[0].length;
        }

        posRef.current = Math.min(next, target);
        forceRender(n => n + 1);
      } else if (!streamingRef.current) {
        clearInterval(id);
      }
    }, TICK_MS);

    return () => clearInterval(id);
  }, []);

  return fullText.slice(0, posRef.current);
}
