/* Shared timeline (presentational): ordered events with timestamps.
 * Order and content come from props exactly as passed. */

export interface TimelineItem {
  id: string;
  time: string;
  title: string;
  detail?: string;
}

export function Timeline({ items }: { items: TimelineItem[] }) {
  if (items.length === 0) {
    return <p className="muted">No events.</p>;
  }
  return (
    <ol className="timeline">
      {items.map((item) => (
        <li key={item.id} className="timeline-item">
          <div className="timeline-time muted">{item.time}</div>
          <div className="timeline-title">{item.title}</div>
          {item.detail !== undefined && item.detail !== "" && (
            <div className="timeline-detail muted">{item.detail}</div>
          )}
        </li>
      ))}
    </ol>
  );
}
