/* World Atlas viewport controls: zoom in/out, reset view, and the
 * selected-region readout. All state lives in the shared
 * GlobeController; this component only dispatches and displays. */

"use client";

import { useSyncExternalStore } from "react";
import { useTranslation } from "../../lib/i18n/context";
import {
  BUTTON_ZOOM_STEP,
  type GlobeController,
} from "./scene/controls";
import { REGION_HUBS } from "./scene/earth";

interface Props {
  controller: GlobeController;
}

export function GlobeControls({ controller }: Props) {
  const { t } = useTranslation("landing");
  const state = useSyncExternalStore(
    (notify) => controller.subscribe(notify),
    () => controller.getState(),
    // Prerender snapshot: the controller is never mutated on the
    // server, so its initial state is stable for hydration.
    () => controller.getState()
  );
  const hub =
    state.selected >= 0 && state.selected < REGION_HUBS.length
      ? REGION_HUBS[state.selected]
      : undefined;

  return (
    <div className="globe-controls" role="group" aria-label={t("globeControls")}>
      <p className="visually-hidden" id="globe-hint">
        {t("globeHint")}
      </p>
      <button
        type="button"
        className="landing-control-btn"
        aria-label={t("zoomIn")}
        onClick={() => controller.zoomBy(-BUTTON_ZOOM_STEP)}
      >
        <span aria-hidden="true">+</span>
      </button>
      <button
        type="button"
        className="landing-control-btn"
        aria-label={t("zoomOut")}
        onClick={() => controller.zoomBy(BUTTON_ZOOM_STEP)}
      >
        <span aria-hidden="true">−</span>
      </button>
      <button
        type="button"
        className="landing-control-btn"
        onClick={() => controller.reset()}
      >
        {t("resetView")}
      </button>
      {hub !== undefined && (
        <p className="globe-region" role="status">
          <span lang="en">{hub.name}</span>
          <span className="globe-region-note">{t("regionSignal")}</span>
          <button
            type="button"
            className="landing-control-btn"
            aria-label={t("closeRegion")}
            onClick={() => controller.select(-1)}
          >
            <span aria-hidden="true">×</span>
          </button>
        </p>
      )}
    </div>
  );
}
