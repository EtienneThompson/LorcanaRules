import type { CardSearchResult } from '../types';

interface Props {
  results: CardSearchResult[];
  activeIndex: number;
  loading: boolean;
  onSelect: (card: CardSearchResult) => void;
  onActiveChange: (index: number) => void;
}

export function CardSearchDropdown({
  results,
  activeIndex,
  loading,
  onSelect,
  onActiveChange,
}: Props) {
  if (!loading && results.length === 0) return null;

  return (
    <div className="absolute bottom-full mb-2 left-0 right-0 z-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg overflow-hidden">
      {loading && results.length === 0 ? (
        <div className="flex items-center justify-center gap-2 px-3 py-3 text-sm text-gray-500 dark:text-gray-400">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.3s]" />
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.15s]" />
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" />
        </div>
      ) : (
        <ul className="max-h-60 overflow-y-auto py-1" role="listbox">
          {results.map((card, i) => (
            <li
              key={card.card_id}
              role="option"
              aria-selected={i === activeIndex}
              className={`flex items-center gap-3 px-3 py-2 cursor-pointer text-sm ${
                i === activeIndex
                  ? 'bg-indigo-50 dark:bg-indigo-900/30'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
              onMouseEnter={() => onActiveChange(i)}
              onMouseDown={e => {
                // Prevent the textarea from losing focus before the click registers.
                e.preventDefault();
                onSelect(card);
              }}
            >
              <img
                src={card.image_url}
                alt={card.full_name}
                className="w-8 h-auto rounded flex-shrink-0"
              />
              <span className="text-gray-900 dark:text-gray-100 font-medium">
                {card.full_name}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
