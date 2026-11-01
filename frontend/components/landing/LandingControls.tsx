/* Landing controls: optional audio toggle + motion control.
 * Audio is OFF by default and starts only on explicit activation. */

"use client";

import { useEffect, useRef, useState } from "react";
import { LandingAudio } from "../../lib/landing-audio";

export function AudioControl({ onBlipRef }: {
  onBlipRef: React.MutableRefObject<(() => void) | null>;
}) {
  const audioRef = useRef<LandingAudio | null>(null);
  const [on, setOn] = useState(false);
  const [volume, setVolume] = useState(0.5);

  useEffect(() => {
    const audio = new LandingAudio();
    audioRef.current = audio;
    onBlipRef.current = () => audio.blip();
    return () => {
      audio.dispose();
      audioRef.current = null;
      onBlipRef.current = null;
    };
  }, [onBlipRef]);

  const toggle = async () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (on) {
      audio.stop();
      setOn(false);
      return;
    }
    const started = await audio.start();
    setOn(started);
  };

  return (
    <div className="landing-audio" role="group" aria-label="Ambient sound">
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={on}
        onClick={() => void toggle()}
      >
        Sound: {on ? "On" : "Off"}
      </button>
      <label className="landing-volume">
        Volume
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={volume}
          disabled={!on}
          onChange={(event) => {
            const value = Number(event.target.value);
            setVolume(value);
            audioRef.current?.setVolume(value);
          }}
        />
      </label>
    </div>
  );
}

export function MotionControl({
  motion,
  paused,
  onMotion,
  onPaused,
}: {
  motion: "full" | "reduced";
  paused: boolean;
  onMotion: (motion: "full" | "reduced") => void;
  onPaused: (paused: boolean) => void;
}) {
  return (
    <div className="landing-motion" role="group" aria-label="Scene motion">
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={motion === "reduced"}
        onClick={() => onMotion(motion === "full" ? "reduced" : "full")}
      >
        {motion === "full" ? "Reduce motion" : "Full motion"}
      </button>
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={paused}
        onClick={() => onPaused(!paused)}
      >
        {paused ? "Resume scene" : "Pause scene"}
      </button>
    </div>
  );
}
