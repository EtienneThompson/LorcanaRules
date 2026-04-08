import { useEffect, useRef, useState } from 'react';

/** Characters to reveal per tick. */
const CHARS_PER_TICK = 1;
/** Milliseconds between ticks — 25ms gives ~40 chars/sec. */
const TICK_MS = 15;

/**
 * Returns a progressively revealed substring of `fullText`, advancing
 * CHARS_PER_TICK characters every TICK_MS milliseconds.
 *
 * The ticker runs for the lifetime of the component. While `streaming` is
 * true it keeps chasing the growing `fullText`; once streaming ends and the
 * display has caught up, the interval stops automatically.
 */
export function useTypewriter(fullText: string, streaming: boolean): string {
  // Use a ref for the display position so the interval callback always reads
  // the latest value without being recreated on every change.
  const posRef = useRef(0);
  const fullTextRef = useRef(fullText);
  const streamingRef = useRef(streaming);

  // Keep refs in sync with latest props.
  useEffect(() => { fullTextRef.current = fullText; }, [fullText]);
  useEffect(() => { streamingRef.current = streaming; }, [streaming]);

  // forceRender is the only way to tell React to re-read posRef each tick.
  const [, forceRender] = useState(0);

  useEffect(() => {
    // Reset when this message component mounts (one instance per message).
    posRef.current = 0;

    const id = setInterval(() => {
      const target = fullTextRef.current.length;

      if (posRef.current < target) {
        posRef.current = Math.min(posRef.current + CHARS_PER_TICK, target);
        forceRender(n => n + 1);
      } else if (!streamingRef.current) {
        // Fully caught up and the stream is done — no more work to do.
        clearInterval(id);
      }
    }, TICK_MS);

    return () => clearInterval(id);
  }, []); // single interval per component lifetime

  return fullText.slice(0, posRef.current);
}
