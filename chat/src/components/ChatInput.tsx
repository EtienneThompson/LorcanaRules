import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { searchCards } from '../api';
import type { CardSearchResult } from '../types';
import { CardSearchDropdown } from './CardSearchDropdown';

interface Props {
  onSend: (text: string, cards: CardSearchResult[]) => void;
  disabled: boolean;
}

interface AutocompleteState {
  results: CardSearchResult[];
  activeIndex: number;
  /** Index in `value` where the opening `[[` starts. */
  startPos: number;
}

/**
 * Finds the unclosed `[[` trigger nearest to the end of the string.
 * Returns the prefix typed after `[[` and its start position,
 * or null if no active trigger exists.
 */
function getActiveTrigger(value: string): { prefix: string; startPos: number } | null {
  const lastOpen = value.lastIndexOf('[[');
  if (lastOpen === -1) return null;
  const afterOpen = value.slice(lastOpen + 2);
  // If the user already closed the bracket, no active trigger.
  if (afterOpen.includes(']]')) return null;
  return { prefix: afterOpen, startPos: lastOpen };
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('');
  const [ac, setAc] = useState<AutocompleteState | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  /** Pending card refs by full_name, accumulated as user inserts cards. */
  const pendingCardsRef = useRef<Map<string, CardSearchResult>>(new Map());
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchAbortRef = useRef<AbortController | null>(null);

  // When value changes, check whether we should trigger autocomplete.
  useEffect(() => {
    const trigger = getActiveTrigger(value);

    if (!trigger) {
      setAc(null);
      setSearchLoading(false);
      return;
    }

    const { prefix, startPos } = trigger;

    if (!prefix) {
      // `[[` typed but no characters yet — open dropdown in loading state.
      setAc({ results: [], activeIndex: 0, startPos });
      setSearchLoading(false);
      return;
    }

    // Show the dropdown immediately in loading state, then fill in results.
    setAc(prev => ({ results: prev?.results ?? [], activeIndex: 0, startPos }));
    setSearchLoading(true);

    // Cancel any in-flight request from the previous keystroke.
    searchAbortRef.current?.abort();
    const abortController = new AbortController();
    searchAbortRef.current = abortController;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      const results = await searchCards(prefix, abortController.signal);
      setAc({ results, activeIndex: 0, startPos });
      setSearchLoading(false);
    }, 200);
  }, [value]);

  const selectCard = useCallback(
    (card: CardSearchResult) => {
      if (!ac) return;
      // Replace everything from `[[` to end-of-typed-prefix with `[[Full Name]]`
      // ac.startPos is where `[[` begins; everything from there to value.length
      // is the `[[prefix` fragment (no `]]` yet, by definition of getActiveTrigger).
      const before = value.slice(0, ac.startPos);
      const newValue = `${before}[[${card.full_name}]]`;
      setValue(newValue);
      pendingCardsRef.current.set(card.full_name, card);
      setAc(null);
      setTimeout(() => textareaRef.current?.focus(), 0);
    },
    [ac, value],
  );

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;

    // Collect all [[Card Name]] references present in the final text.
    const cards: CardSearchResult[] = [];
    const markerRe = /\[\[([^\]]+)\]\]/g;
    let match: RegExpExecArray | null;
    while ((match = markerRe.exec(trimmed)) !== null) {
      const name = match[1];
      const card = pendingCardsRef.current.get(name);
      if (card) cards.push(card);
    }

    onSend(trimmed, cards);
    setValue('');
    pendingCardsRef.current.clear();
    setAc(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (ac && ac.results.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setAc(prev =>
          prev ? { ...prev, activeIndex: (prev.activeIndex + 1) % prev.results.length } : prev,
        );
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setAc(prev =>
          prev
            ? { ...prev, activeIndex: (prev.activeIndex - 1 + prev.results.length) % prev.results.length }
            : prev,
        );
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        const card = ac.results[ac.activeIndex];
        if (card) selectCard(card);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setAc(null);
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }

  return (
    <div className="relative">
      {ac && (
        <CardSearchDropdown
          results={ac.results}
          activeIndex={ac.activeIndex}
          loading={searchLoading}
          onSelect={selectCard}
          onActiveChange={i => setAc(prev => prev ? { ...prev, activeIndex: i } : prev)}
        />
      )}
      <div
        className="flex items-center gap-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl px-4 py-3 shadow-sm cursor-text"
        onClick={() => textareaRef.current?.focus()}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          rows={1}
          placeholder="Ask about Lorcana rules or cards… (type [[ to reference a card)"
          className="flex-1 resize-none bg-transparent text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none leading-relaxed"
          style={{ maxHeight: '200px' }}
        />
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send"
          className="flex-shrink-0 w-8 h-8 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-200 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
        >
          <svg
            className="w-4 h-4 text-white disabled:text-gray-400"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
