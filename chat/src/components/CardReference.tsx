import { useEffect, useRef, useState } from "react";
import type { CardReference as CardReferenceType } from "../types";

interface Props {
  card: CardReferenceType;
}

// Lorcana cards are 63x88mm (~5:7 ratio). At 200px wide the natural height is ~280px.
const ESTIMATED_TOOLTIP_HEIGHT = 280 + 16; // image + padding

export function CardReference({ card }: Props) {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [above, setAbove] = useState(true);
  const triggerRef = useRef<HTMLSpanElement>(null);

  function calcPosition() {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setAbove(rect.top >= ESTIMATED_TOOLTIP_HEIGHT);
    }
  }

  function handleMouseEnter() {
    if (!pinned) {
      calcPosition();
      setOpen(true);
    }
  }

  function handleMouseLeave() {
    if (!pinned) {
      setOpen(false);
    }
  }

  function handleClick(e: React.MouseEvent) {
    e.stopPropagation();
    if (pinned) {
      setPinned(false);
      setOpen(false);
    } else {
      calcPosition();
      setPinned(true);
      setOpen(true);
    }
  }

  // Dismiss on any click outside when pinned.
  useEffect(() => {
    if (!pinned) return;
    function onDocClick() {
      setPinned(false);
      setOpen(false);
    }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, [pinned]);

  return (
    <span className="relative inline-block">
      <span
        ref={triggerRef}
        className="font-semibold text-indigo-600 dark:text-indigo-400 underline decoration-dotted underline-offset-2 cursor-pointer"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        tabIndex={0}
        role="button"
        aria-label={`Card: ${card.full_name}`}
        aria-expanded={open}
      >
        {card.full_name}
      </span>

      {open && (
        <span
          className={`absolute left-1/2 -translate-x-1/2 z-10 p-2 w-[216px] leading-[0] rounded-lg bg-gray-900 dark:bg-gray-700 shadow-lg pointer-events-none block ${
            above ? "bottom-full mb-2" : "top-full mt-2"
          }`}
        >
          <img
            src={card.image_url}
            alt={card.full_name}
            className="not-prose w-[200px] h-auto rounded block"
          />
          {above ? (
            <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700" />
          ) : (
            <span className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900 dark:border-b-gray-700" />
          )}
        </span>
      )}
    </span>
  );
}
