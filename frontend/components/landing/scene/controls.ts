/* World Atlas view state: user rotation, zoom, and region selection.
 * Pure TypeScript (no DOM, no three.js) so every interaction rule is
 * unit-tested; GlobalHeroScene and GlobeControls only wire it up. */

export const DRAG_RAD_PER_PX = 0.005;
export const KEY_YAW_STEP = 0.12;
export const KEY_PITCH_STEP = 0.08;
export const KEY_ZOOM_STEP = 0.5;
export const BUTTON_ZOOM_STEP = 0.6;
export const WHEEL_ZOOM_PER_DELTA = 0.002;
export const PINCH_ZOOM_PER_PX = 0.01;
export const CLICK_MAX_TRAVEL_PX = 6;

/** Pitch clamp (radians): the globe never flips past its poles. */
export const PITCH_MIN = -0.55;
export const PITCH_MAX = 0.55;
/** Zoom clamp (camera-distance offset, world units). */
export const ZOOM_MIN = -1.6;
export const ZOOM_MAX = 2.2;

export interface GlobeViewState {
  /** User yaw offset (radians, added to auto-rotation). */
  yaw: number;
  /** User pitch offset (radians, clamped). */
  pitch: number;
  /** Camera distance offset (world units, clamped). */
  zoom: number;
  /** Selected region-hub index, or -1 for none. */
  selected: number;
}

const INITIAL: GlobeViewState = { yaw: 0, pitch: 0, zoom: 0, selected: -1 };

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export class GlobeController {
  private state: GlobeViewState = { ...INITIAL };
  private listeners = new Set<() => void>();

  getState(): GlobeViewState {
    return this.state;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emit(): void {
    this.listeners.forEach((listener) => listener());
  }

  /** Drag rotation: rightward drags turn the globe right, upward pitch up. */
  addRotation(dxPx: number, dyPx: number): void {
    this.state = {
      ...this.state,
      yaw: this.state.yaw + dxPx * DRAG_RAD_PER_PX,
      pitch: clamp(
        this.state.pitch + dyPx * DRAG_RAD_PER_PX,
        PITCH_MIN,
        PITCH_MAX
      ),
    };
    this.emit();
  }

  /** Keyboard nudge in radians (already-scaled steps). */
  nudge(dyaw: number, dpitch: number): void {
    this.state = {
      ...this.state,
      yaw: this.state.yaw + dyaw,
      pitch: clamp(this.state.pitch + dpitch, PITCH_MIN, PITCH_MAX),
    };
    this.emit();
  }

  /** Positive delta dollies out, negative dollies in. */
  zoomBy(delta: number): void {
    const zoom = clamp(this.state.zoom + delta, ZOOM_MIN, ZOOM_MAX);
    if (zoom === this.state.zoom) return;
    this.state = { ...this.state, zoom };
    this.emit();
  }

  select(index: number): void {
    if (index === this.state.selected) return;
    this.state = { ...this.state, selected: index };
    this.emit();
  }

  reset(): void {
    this.state = { ...INITIAL };
    this.emit();
  }
}

/** Keyboard map for the atlas viewport. Returns true when handled. */
export function handleGlobeKey(
  key: string,
  controller: GlobeController,
  hubCount: number
): boolean {
  switch (key) {
    case "ArrowLeft":
      controller.nudge(-KEY_YAW_STEP, 0);
      return true;
    case "ArrowRight":
      controller.nudge(KEY_YAW_STEP, 0);
      return true;
    case "ArrowUp":
      controller.nudge(0, KEY_PITCH_STEP);
      return true;
    case "ArrowDown":
      controller.nudge(0, -KEY_PITCH_STEP);
      return true;
    case "+":
    case "=":
      controller.zoomBy(-KEY_ZOOM_STEP);
      return true;
    case "-":
    case "_":
      controller.zoomBy(KEY_ZOOM_STEP);
      return true;
    case "0":
      controller.reset();
      return true;
    case "Escape":
      controller.select(-1);
      return true;
    default:
      break;
  }
  // Digit1..Digit8 select a region hub (also plain "1".."8" code).
  const digit = /^[1-8]$/.exec(key);
  if (digit) {
    const index = Number(digit[0]) - 1;
    if (index < hubCount) {
      controller.select(index);
      return true;
    }
  }
  return false;
}
