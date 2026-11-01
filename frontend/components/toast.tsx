/* Shared toast region (presentational): the parent owns the message
 * list and lifetime; this only renders them with the correct live
 * roles. Errors use role=alert, successes role=status. */

export interface ToastMessage {
  id: string;
  text: string;
  tone: "ok" | "error";
}

export function ToastRegion({ messages }: { messages: ToastMessage[] }) {
  return (
    <div className="toast-region" aria-live="polite">
      {messages.map((message) => (
        <div
          key={message.id}
          role={message.tone === "error" ? "alert" : "status"}
          className={`toast toast-${message.tone}`}
        >
          {message.text}
        </div>
      ))}
    </div>
  );
}
