import { afterEach, describe, expect, it, vi } from "vitest";
import { LandingAudio } from "./landing-audio";

function mockAudioContext() {
  const nodes: { stop?: () => void; disconnect: () => void }[] = [];
  const makeParam = () => ({
    value: 0,
    setValueAtTime: vi.fn(),
    exponentialRampToValueAtTime: vi.fn(),
    linearRampToValueAtTime: vi.fn(),
    setTargetAtTime: vi.fn(),
    cancelScheduledValues: vi.fn(),
  });
  const context = {
    currentTime: 0,
    destination: {},
    resume: vi.fn().mockResolvedValue(undefined),
    close: vi.fn().mockResolvedValue(undefined),
    createGain: vi.fn(() => {
      const node = { gain: makeParam(), connect: vi.fn(), disconnect: vi.fn() };
      nodes.push(node);
      return node;
    }),
    createOscillator: vi.fn(() => {
      const node = {
        type: "",
        frequency: makeParam(),
        detune: makeParam(),
        connect: vi.fn(),
        disconnect: vi.fn(),
        start: vi.fn(),
        stop: vi.fn(),
      };
      nodes.push(node);
      return node;
    }),
    createBiquadFilter: vi.fn(() => {
      const node = {
        type: "",
        frequency: makeParam(),
        connect: vi.fn(),
        disconnect: vi.fn(),
      };
      nodes.push(node);
      return node;
    }),
  };
  return context;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("LandingAudio", () => {
  it("is OFF by default and silent without an AudioContext", async () => {
    const audio = new LandingAudio();
    expect(audio.playing).toBe(false);
    expect(await audio.start()).toBe(false);
    expect(() => audio.blip()).not.toThrow();
    audio.dispose();
  });

  it("starts, adjusts volume, blips, and stops cleanly", async () => {
    const context = mockAudioContext();
    vi.stubGlobal("AudioContext", vi.fn(() => context));
    const audio = new LandingAudio();
    expect(await audio.start()).toBe(true);
    expect(audio.playing).toBe(true);
    expect(context.resume).toHaveBeenCalled();
    audio.setVolume(0.2);
    expect(() => audio.blip()).not.toThrow();
    expect(() => audio.stop()).not.toThrow();
    expect(audio.playing).toBe(false);
    audio.dispose();
    expect(context.close).toHaveBeenCalled();
  });

  it("fades in on start and schedules crystalline plucks", async () => {
    vi.useFakeTimers();
    const context = mockAudioContext();
    vi.stubGlobal("AudioContext", vi.fn(() => context));
    const audio = new LandingAudio();
    await audio.start();
    // Fade-in ramp programmed on the master bus.
    const master = context.createGain.mock.results[0]?.value as {
      gain: { linearRampToValueAtTime: (...a: unknown[]) => void };
    };
    expect(master.gain.linearRampToValueAtTime).toHaveBeenCalled();
    // Pad (3) + filter LFO + tremolo = 5 oscillators at start.
    expect(context.createOscillator).toHaveBeenCalledTimes(5);
    // Advancing past the pluck interval adds a pluck voice.
    await vi.advanceTimersByTimeAsync(2300);
    expect(context.createOscillator).toHaveBeenCalledTimes(6);
    audio.dispose();
  });

  it("mutes without stopping, then fades out on stop", async () => {
    vi.useFakeTimers();
    const context = mockAudioContext();
    vi.stubGlobal("AudioContext", vi.fn(() => context));
    const audio = new LandingAudio();
    await audio.start();
    audio.setMuted(true);
    expect(audio.isMuted()).toBe(true);
    expect(audio.playing).toBe(true);
    const master = context.createGain.mock.results[0]?.value as {
      gain: { setTargetAtTime: (...a: unknown[]) => void };
    };
    expect(master.gain.setTargetAtTime).toHaveBeenCalled();
    audio.setMuted(false);
    expect(audio.isMuted()).toBe(false);
    audio.stop();
    expect(audio.playing).toBe(false);
    // Nodes release after the fade-out tail, not synchronously.
    audio.dispose();
  });
});
