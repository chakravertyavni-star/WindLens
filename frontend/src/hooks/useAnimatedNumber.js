import { useEffect, useState } from "react";

function prefersReducedMotion() {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Count-up animation for numeric KPIs; instant when reduced-motion is set. */
export function useAnimatedNumber(value, durationMs = 700) {
  const [display, setDisplay] = useState(value ?? 0);

  useEffect(() => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      setDisplay(0);
      return;
    }
    if (prefersReducedMotion()) {
      setDisplay(value);
      return;
    }
    const start = display;
    const delta = value - start;
    if (Math.abs(delta) < 0.5) {
      setDisplay(value);
      return;
    }
    const t0 = performance.now();
    let frame;
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / durationMs);
      const eased = 1 - (1 - p) ** 3;
      setDisplay(start + delta * eased);
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- animate from current display
  }, [value, durationMs]);

  return display;
}
