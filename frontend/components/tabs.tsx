"use client";

/* Shared accessible tabs (WAI-APG automatic activation): click or arrow
 * keys select a tab; Home/End jump. Only the active panel renders. */

import { useId, useRef, useState } from "react";

export interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
}

export function Tabs({ tabs, label }: { tabs: Tab[]; label: string }) {
  const [active, setActive] = useState(0);
  const base = useId();
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);

  function onKeyDown(ev: React.KeyboardEvent) {
    let next: number | null = null;
    if (ev.key === "ArrowRight") next = (active + 1) % tabs.length;
    else if (ev.key === "ArrowLeft")
      next = (active - 1 + tabs.length) % tabs.length;
    else if (ev.key === "Home") next = 0;
    else if (ev.key === "End") next = tabs.length - 1;
    if (next === null) return;
    ev.preventDefault();
    setActive(next);
    buttons.current[next]?.focus();
  }

  if (tabs.length === 0) return null;
  const current = tabs[active] ?? tabs[0];

  return (
    <div className="tabs">
      <div
        role="tablist"
        aria-label={label}
        className="tablist"
        onKeyDown={onKeyDown}
      >
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => {
              buttons.current[index] = el;
            }}
            type="button"
            role="tab"
            id={`${base}-tab-${tab.id}`}
            aria-selected={index === active}
            aria-controls={`${base}-panel-${tab.id}`}
            tabIndex={index === active ? 0 : -1}
            className="tab"
            onClick={() => setActive(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id={`${base}-panel-${current.id}`}
        aria-labelledby={`${base}-tab-${current.id}`}
        className="tabpanel"
        tabIndex={0}
      >
        {current.content}
      </div>
    </div>
  );
}
