import Link from "next/link";

/* Branded 404: honest directions instead of the default page. */
export default function NotFound() {
  return (
    <div className="card command-section">
      <h2>Page not found</h2>
      <p className="muted">No demo screen lives at this address.</p>
      <p>
        <Link href="/demo">Open the demo</Link> ·{" "}
        <Link href="/">Back to start</Link>
      </p>
    </div>
  );
}
