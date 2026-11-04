"use client";

/* Route error boundary: branded recovery instead of a blank crash.
 * Offers retry; shows the digest ref when Next provides one. Never
 * leaks stack traces (server detail stays in logs). */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="card command-section" role="alert">
      <h2>Something failed to load</h2>
      <p className="muted">
        The demo state is intact — this page hit a rendering error
        {error?.digest ? ` (ref ${error.digest})` : ""}.
      </p>
      <button type="button" className="btn-secondary" onClick={() => reset()}>
        Try again
      </button>
    </div>
  );
}
