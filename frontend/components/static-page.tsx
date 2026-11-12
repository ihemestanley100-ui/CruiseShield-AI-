import Link from "next/link";

/* Shared renderer for static product pages (help, support, legal,
 * privacy). Content is literal English source strings, matching the
 * branded not-found page; translation follows the UGLS kit process.
 * Pages cross-link each other so none is orphaned. */

export interface StaticSection {
  heading: string;
  paragraphs: string[];
}

export function StaticPage({
  title,
  intro,
  sections,
  updated,
}: {
  title: string;
  intro: string;
  sections: StaticSection[];
  updated: string;
}) {
  return (
    <div className="card command-section">
      <h2>{title}</h2>
      <p className="muted">{intro}</p>
      {sections.map((section) => (
        <section key={section.heading}>
          <h3>{section.heading}</h3>
          {section.paragraphs.map((body) => (
            <p key={body.slice(0, 32)}>{body}</p>
          ))}
        </section>
      ))}
      <p className="muted">Last updated: {updated}</p>
      <nav aria-label="Product information">
        <Link href="/help">Help</Link> · <Link href="/support">Support</Link>{" "}
        · <Link href="/legal">Legal</Link> ·{" "}
        <Link href="/privacy">Privacy</Link> ·{" "}
        <Link href="/platform">Platform</Link> · <Link href="/">Start</Link>
      </nav>
    </div>
  );
}
