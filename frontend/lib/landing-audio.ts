/* CruiseShield AI ambient sound identity. Original synthesized
 * soundscape, browser-native Web Audio only: no samples, no
 * libraries, no network, no copyrighted material.
 *
 * Character: a warm detuned pad breathing through a slow filter, a
 * barely-there tremolo pulse, and soft crystalline pentatonic plucks
 * drifting above it. OFF by default; starts only after explicit
 * user activation, with smooth fades in both directions. */

const FADE_IN_SECONDS = 1.2;
const FADE_OUT_MS = 550;
const PLUCK_EVERY_MS = 2200;
/* Gentle pentatonic arc (C5 D5 E5 G5 A5), looping up and down. */
const PLUCK_SCALE = [
  523.25, 587.33, 659.25, 783.99, 880.0, 783.99, 659.25, 587.33,
];

export class LandingAudio {
  private context: AudioContext | null = null;
  private master: GainNode | null = null;
  private nodes: AudioNode[] = [];
  private pluckTimer: ReturnType<typeof setTimeout> | null = null;
  private fadeTimer: ReturnType<typeof setTimeout> | null = null;
  private pluckStep = 0;
  private volume = 0.5;
  private muted = false;
  playing = false;

  private ensureContext(): AudioContext | null {
    if (typeof window === "undefined") return null;
    const Ctor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!Ctor) return null;
    if (!this.context) {
      this.context = new Ctor();
      this.master = this.context.createGain();
      this.master.gain.value = 0;
      this.master.connect(this.context.destination);
    }
    return this.context;
  }

  private targetLevel(): number {
    return this.muted ? 0 : this.volume * 0.16;
  }

  async start(): Promise<boolean> {
    if (this.playing) return true;
    // Restarting mid-fade: finish the old teardown immediately.
    if (this.fadeTimer !== null) {
      clearTimeout(this.fadeTimer);
      this.fadeTimer = null;
      this.teardown();
    }
    const context = this.ensureContext();
    if (!context || !this.master) return false;
    try {
      await context.resume();
    } catch {
      return false;
    }
    const master = this.master;
    // Smooth fade-in from silence.
    try {
      master.gain.cancelScheduledValues(context.currentTime);
      master.gain.setValueAtTime(0.0001, context.currentTime);
      master.gain.linearRampToValueAtTime(
        Math.max(this.targetLevel(), 0.0001),
        context.currentTime + FADE_IN_SECONDS
      );
    } catch {
      master.gain.value = this.targetLevel();
    }
    // Soft detuned pad through a slowly breathing lowpass filter.
    const filter = context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 320;
    const padGain = context.createGain();
    padGain.gain.value = 0.9;
    filter.connect(padGain);
    padGain.connect(master);
    const lfo = context.createOscillator();
    lfo.frequency.value = 0.08;
    const lfoGain = context.createGain();
    lfoGain.gain.value = 120;
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);
    lfo.start();
    // Barely-there tremolo: the pad gently swells ~6x/minute.
    const tremolo = context.createOscillator();
    tremolo.type = "sine";
    tremolo.frequency.value = 0.1;
    const tremoloGain = context.createGain();
    tremoloGain.gain.value = 0.12;
    tremolo.connect(tremoloGain);
    tremoloGain.connect(padGain.gain);
    tremolo.start();
    for (const [freq, detune] of [[110, 0], [164.81, 4], [220, -5]] as const) {
      const osc = context.createOscillator();
      osc.type = "sine";
      osc.frequency.value = freq;
      osc.detune.value = detune;
      osc.connect(filter);
      osc.start();
      this.nodes.push(osc);
    }
    this.nodes.push(filter, padGain, lfo, lfoGain, tremolo, tremoloGain);
    // Crystalline plucks on their own soft bus.
    const shimmer = context.createGain();
    shimmer.gain.value = 0.5;
    shimmer.connect(master);
    this.nodes.push(shimmer);
    this.playing = true;
    this.schedulePluck(context, shimmer);
    return true;
  }

  private schedulePluck(context: AudioContext, bus: GainNode): void {
    this.pluckTimer = setTimeout(() => {
      this.pluckTimer = null;
      if (!this.playing) return;
      try {
        const osc = context.createOscillator();
        osc.type = "triangle";
        osc.frequency.value =
          PLUCK_SCALE[this.pluckStep++ % PLUCK_SCALE.length] ?? 523.25;
        const gain = context.createGain();
        gain.gain.setValueAtTime(0.05, context.currentTime);
        gain.gain.exponentialRampToValueAtTime(
          0.0001, context.currentTime + 1.6
        );
        osc.connect(gain);
        gain.connect(bus);
        osc.start();
        osc.stop(context.currentTime + 1.7);
      } catch {
        // Audio is decorative; never throw into timers.
      }
      this.schedulePluck(context, bus);
    }, PLUCK_EVERY_MS);
  }

  /** Short interface blip for CTA hover/press (only while audible). */
  blip(): void {
    const context = this.context;
    if (!context || !this.playing || !this.master || this.muted) return;
    try {
      const osc = context.createOscillator();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(660, context.currentTime);
      osc.frequency.exponentialRampToValueAtTime(
        440, context.currentTime + 0.14
      );
      const gain = context.createGain();
      gain.gain.setValueAtTime(0.12 * this.volume, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(
        0.001, context.currentTime + 0.16
      );
      osc.connect(gain);
      gain.connect(this.master);
      osc.start();
      osc.stop(context.currentTime + 0.18);
    } catch {
      // Audio is decorative; never throw into UI handlers.
    }
  }

  setVolume(value: number): void {
    this.volume = Math.min(1, Math.max(0, value));
    this.applyLevel();
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
    this.applyLevel();
  }

  isMuted(): boolean {
    return this.muted;
  }

  private applyLevel(): void {
    if (this.master && this.context && this.playing) {
      try {
        this.master.gain.setTargetAtTime(
          Math.max(this.targetLevel(), 0.0001),
          this.context.currentTime,
          0.08
        );
      } catch {
        this.master.gain.value = this.targetLevel();
      }
    }
  }

  stop(): void {
    if (!this.playing && this.nodes.length === 0) return;
    this.playing = false;
    if (this.pluckTimer !== null) {
      clearTimeout(this.pluckTimer);
      this.pluckTimer = null;
    }
    // Fade out, then release the graph after the tail dies.
    if (this.master && this.context) {
      try {
        this.master.gain.cancelScheduledValues(this.context.currentTime);
        this.master.gain.setTargetAtTime(
          0.0001, this.context.currentTime, 0.15
        );
      } catch {
        // Fall through to immediate teardown below.
        this.teardown();
        return;
      }
    }
    if (this.fadeTimer !== null) clearTimeout(this.fadeTimer);
    this.fadeTimer = setTimeout(() => {
      this.fadeTimer = null;
      this.teardown();
    }, FADE_OUT_MS);
  }

  private teardown(): void {
    for (const node of this.nodes) {
      try {
        (node as OscillatorNode).stop?.();
      } catch {
        // Already stopped; ignore.
      }
      try {
        node.disconnect();
      } catch {
        // Already disconnected; ignore.
      }
    }
    this.nodes = [];
  }

  dispose(): void {
    if (this.pluckTimer !== null) {
      clearTimeout(this.pluckTimer);
      this.pluckTimer = null;
    }
    if (this.fadeTimer !== null) {
      clearTimeout(this.fadeTimer);
      this.fadeTimer = null;
    }
    this.playing = false;
    this.teardown();
    try {
      void this.context?.close();
    } catch {
      // Ignore close errors during teardown.
    }
    this.context = null;
    this.master = null;
  }
}
