import { useState } from 'react';
import type { Citation } from '../types';

interface Props {
  citation: Citation;
}

export function CitationBadge({ citation }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block align-middle mx-0.5">
      <button
        className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-[10px] font-bold leading-none cursor-pointer hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        aria-label={`Citation ${citation.number}: Rule ${citation.rule_id}`}
      >
        {citation.number}
      </button>

      {open && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-10 w-72 rounded-lg bg-gray-900 dark:bg-gray-700 text-white text-xs px-3 py-2 shadow-lg pointer-events-none">
          <span className="block font-semibold text-indigo-300 mb-1">
            Rule {citation.rule_id}
          </span>
          <span className="block leading-relaxed text-gray-200">
            {citation.rule_text || 'Rule text unavailable.'}
          </span>
          {/* Arrow */}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700" />
        </span>
      )}
    </span>
  );
}
