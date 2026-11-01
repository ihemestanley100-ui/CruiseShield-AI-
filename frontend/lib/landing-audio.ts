/* Optional synthesized ambience for the landing page. Browser-native
 * Web Audio only: no samples, no libraries, no network. OFF by default;
 * starts only after explicit user activation. */

export class LandingAudio {
  private context: AudioContext | null = null;
  private master: GainNode | null = null;
  private nodes: AudioNode[] = [];
  private volume = 0.5;
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
      this.master.gain.value = this.volume * 0.16;
      this.master.connect(this.context.destination);
    }
    return this.context;
  }

  async start(): Promise<boolean> {
    if (this.playing) return true;
    const context = this.ensureContext();
    if (!context || !this.master) return false;
    try {
      await context.resume();
    } catch {
      return false;
    }
    // Soft detuned pad through a slowly breathing lowpass filter.
    const filter = context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 320;
    filter.connect(this.master);
    const lfo = context.createOscillator();
    lfo.frequency.value = 0.08;
    const lfoGain = context.createGain();
    lfoGain.gain.value = 120;
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);
    lfo.start();
    for (const [freq, detune] of [[110, 0], [164.81, 4], [220, -5]] as const) {
      const osc = context.createOscillator();
      osc.type = "sine";
      osc.frequency.value = freq;
      osc.detune.value = detune;
      osc.connect(filter);
      osc.start();
      this.nodes.push(osc);
    }
    this.nodes.push(filter, lfo, lfoGain);
    this.playing = true;
    return true;
  }

  /** Short interface blip for CTA hover/press (only while playing). */
  blip(): void {
    const context = this.context;
    if (!context || !this.playing || !this.master) return;
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
    if (this.master && this.context) {
      this.master.gain.setValueAtTime(
        this.volume * 0.16, this.context.currentTime
      );
    }
  }

  stop(): void {
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
    this.playing = false;
  }

  dispose(): void {
    this.stop();
    try {
      void this.context?.close();
    } catch {
      // Ignore close errors during teardown.
    }
    this.context = null;
    this.master = null;
  }
}
