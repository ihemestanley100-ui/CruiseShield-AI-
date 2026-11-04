/* Landing controls: optional audio toggle + motion control.
 * Audio is OFF by default and starts only on explicit activation. */

"use client";

import { useEffect, useRef, useState } from "react";
import { LandingAudio } from "../../lib/landing-audio";
import { useTranslation } from "../../lib/i18n/context";

export function AudioControl({ onBlipRef }: {
  onBlipRef: React.MutableRefObject<(() => void) | null>;
}) {
  const audioRef = useRef<LandingAudio | null>(null);
  const { t } = useTranslation("landing");
  const [on, setOn] = useState(false);
  const [muted, setMuted] = useState(false);
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
    <div className="landing-audio" role="group" aria-label={t("controlsAmbient")}>
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={on}
        onClick={() => void toggle()}
      >
        {t("soundLabel")}: {on ? t("onWord") : t("offWord")}
      </button>
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={muted}
        disabled={!on}
        onClick={() => {
          const next = !muted;
          setMuted(next);
          audioRef.current?.setMuted(next);
        }}
      >
        {muted ? t("unmute") : t("mute")}
      </button>
      <label className="landing-volume">
        {t("volumeLabel")}
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
  const { t } = useTranslation("landing");
  return (
    <div className="landing-motion" role="group" aria-label={t("sceneMotion")}>
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={motion === "reduced"}
        onClick={() => onMotion(motion === "full" ? "reduced" : "full")}
      >
        {motion === "full" ? t("reduceMotion") : t("fullMotion")}
      </button>
      <button
        type="button"
        className="landing-control-btn"
        aria-pressed={paused}
        onClick={() => onPaused(!paused)}
      >
        {paused ? t("resumeScene") : t("pauseScene")}
      </button>
    </div>
  );
}
