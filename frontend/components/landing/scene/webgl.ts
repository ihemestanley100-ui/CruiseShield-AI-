/* WebGL availability probe (testable, no renderer side effects). */

export function isWebGLAvailable(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    const context =
      canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    if (!context) return false;
    // Release the probe context immediately.
    const lose = (context as WebGLRenderingContext).getExtension(
      "WEBGL_lose_context"
    );
    lose?.loseContext();
    return true;
  } catch {
    return false;
  }
}

/* True unless the page is hidden (safe default when document is absent). */
export function isPageVisible(): boolean {
  if (typeof document === "undefined") return true;
  return document.visibilityState !== "hidden";
}
