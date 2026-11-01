"use client";

/* On-page section navigation for long walkthrough pages. Plain anchor
 * links (keyboard accessible, no JS required to navigate); a small
 * IntersectionObserver adds aria-current + .active to the section in
 * view. When IntersectionObserver is unavailable the links still work
 * and no item claims to be current. */

import { useEffect, useState } from "react";

export interface SectionNavItem {
  id: string;
  label: string;
}

export function SectionNav({ items }: { items: SectionNavItem[] }) {
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const targets = items
      .map((item) => document.getElementById(item.id))
      .filter((el): el is HTMLElement => el !== null);
    if (targets.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) setActive(entry.target.id);
        }
      },
      { rootMargin: "-25% 0px -65% 0px" }
    );
    for (const target of targets) observer.observe(target);
    return () => observer.disconnect();
    // Depend on the id list, not the array identity: parents pass an
    // inline literal, and resubscribing every render would churn.
  }, [items.map((item) => item.id).join(",")]);

  return (
    <nav aria-label="On this page" className="section-nav-wrap">
      <ul className="section-nav">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              aria-current={active === item.id ? "true" : undefined}
              className={active === item.id ? "active" : undefined}
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
