/* Route loading state: static, honest, no fake progress.
 * No animation by design (reduced-motion safe); shown during
 * cold starts and slow fetches while layout + shell persist. */
export default function Loading() {
  return (
    <div className="card command-section" aria-busy="true" aria-live="polite">
      <h2>Loading</h2>
      <p className="muted">Fetching the latest workspace state.</p>
    </div>
  );
}
