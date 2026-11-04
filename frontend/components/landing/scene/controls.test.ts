import { describe, expect, it, vi } from "vitest";
import {
  BUTTON_ZOOM_STEP,
  CLICK_MAX_TRAVEL_PX,
  DRAG_RAD_PER_PX,
  GlobeController,
  KEY_PITCH_STEP,
  KEY_YAW_STEP,
  KEY_ZOOM_STEP,
  PITCH_MAX,
  PITCH_MIN,
  ZOOM_MAX,
  ZOOM_MIN,
  handleGlobeKey,
} from "./controls";

describe("GlobeController", () => {
  it("starts centered, unzoomed, with no selection", () => {
    const state = new GlobeController().getState();
    expect(state).toEqual({ yaw: 0, pitch: 0, zoom: 0, selected: -1 });
    expect(CLICK_MAX_TRAVEL_PX).toBeGreaterThan(0);
    expect(BUTTON_ZOOM_STEP).toBeGreaterThan(0);
  });

  it("accumulates drag rotation and clamps pitch at the poles", () => {
    const controller = new GlobeController();
    controller.addRotation(100, 40);
    let state = controller.getState();
    expect(state.yaw).toBeCloseTo(100 * DRAG_RAD_PER_PX, 9);
    expect(state.pitch).toBeCloseTo(40 * DRAG_RAD_PER_PX, 9);
    controller.addRotation(0, 100000);
    state = controller.getState();
    expect(state.pitch).toBe(PITCH_MAX);
    controller.addRotation(0, -200000);
    expect(controller.getState().pitch).toBe(PITCH_MIN);
  });

  it("clamps zoom to the camera corridor", () => {
    const controller = new GlobeController();
    controller.zoomBy(-100);
    expect(controller.getState().zoom).toBe(ZOOM_MIN);
    controller.zoomBy(100);
    expect(controller.getState().zoom).toBe(ZOOM_MAX);
  });

  it("selects and clears regions, and resets everything", () => {
    const controller = new GlobeController();
    controller.select(3);
    expect(controller.getState().selected).toBe(3);
    controller.select(-1);
    expect(controller.getState().selected).toBe(-1);
    controller.addRotation(50, 10);
    controller.zoomBy(1);
    controller.select(2);
    controller.reset();
    expect(controller.getState()).toEqual({
      yaw: 0,
      pitch: 0,
      zoom: 0,
      selected: -1,
    });
  });

  it("notifies subscribers on change and stops after unsubscribe", () => {
    const controller = new GlobeController();
    const listener = vi.fn();
    const off = controller.subscribe(listener);
    controller.zoomBy(0.2);
    expect(listener).toHaveBeenCalledTimes(1);
    off();
    controller.zoomBy(0.2);
    expect(listener).toHaveBeenCalledTimes(1);
  });
});

describe("handleGlobeKey", () => {
  it("maps arrows, zoom, reset, and digits to controller calls", () => {
    const controller = new GlobeController();
    expect(handleGlobeKey("ArrowRight", controller, 8)).toBe(true);
    expect(controller.getState().yaw).toBeCloseTo(KEY_YAW_STEP, 9);
    expect(handleGlobeKey("ArrowLeft", controller, 8)).toBe(true);
    expect(controller.getState().yaw).toBeCloseTo(0, 9);
    expect(handleGlobeKey("ArrowUp", controller, 8)).toBe(true);
    expect(controller.getState().pitch).toBeCloseTo(KEY_PITCH_STEP, 9);
    expect(handleGlobeKey("ArrowDown", controller, 8)).toBe(true);
    expect(controller.getState().pitch).toBeCloseTo(0, 9);
    expect(handleGlobeKey("+", controller, 8)).toBe(true);
    expect(controller.getState().zoom).toBeCloseTo(-KEY_ZOOM_STEP, 9);
    expect(handleGlobeKey("-", controller, 8)).toBe(true);
    expect(controller.getState().zoom).toBeCloseTo(0, 9);
    expect(handleGlobeKey("3", controller, 8)).toBe(true);
    expect(controller.getState().selected).toBe(2);
    expect(handleGlobeKey("Escape", controller, 8)).toBe(true);
    expect(controller.getState().selected).toBe(-1);
    controller.zoomBy(1);
    expect(handleGlobeKey("0", controller, 8)).toBe(true);
    expect(controller.getState().zoom).toBe(0);
  });

  it("ignores out-of-range digits and unmapped keys", () => {
    const controller = new GlobeController();
    expect(handleGlobeKey("8", controller, 4)).toBe(false);
    expect(handleGlobeKey("9", controller, 8)).toBe(false);
    expect(handleGlobeKey("Enter", controller, 8)).toBe(false);
    expect(controller.getState()).toEqual({
      yaw: 0,
      pitch: 0,
      zoom: 0,
      selected: -1,
    });
  });
});
