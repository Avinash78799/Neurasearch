import { useEffect, useState, useRef } from "react";

export default function CursorMotion() {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [trailingPos, setTrailingPos] = useState({ x: -100, y: -100 });
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [ripples, setRipples] = useState([]);

  const posRef = useRef({ x: -100, y: -100 });
  const trailingRef = useRef({ x: -100, y: -100 });
  const animFrameId = useRef(null);

  useEffect(() => {
    // Disable custom cursor on touch devices to avoid interference
    if (typeof window !== "undefined" && "ontouchstart" in window) {
      return;
    }

    const handleMouseMove = (e) => {
      if (!isVisible) setIsVisible(true);
      posRef.current = { x: e.clientX, y: e.clientY };
      setPosition({ x: e.clientX, y: e.clientY });

      // Check if mouse is hovering over an interactive element
      const target = e.target;
      const isInteractive =
        target.closest("button") ||
        target.closest("a") ||
        target.closest("input") ||
        target.closest("textarea") ||
        target.closest("[role='button']") ||
        target.closest(".interactive") ||
        target.closest(".glass");

      setIsHovered(!!isInteractive);
    };

    const handleMouseDown = () => {
      setIsClicked(true);
      const newRipple = {
        id: Date.now(),
        x: posRef.current.x,
        y: posRef.current.y,
      };
      setRipples((prev) => [...prev.slice(-4), newRipple]);
      setTimeout(() => setIsClicked(false), 200);
    };

    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    // Smooth trailing physics animation loop (lerp)
    const animateTrailing = () => {
      trailingRef.current.x += (posRef.current.x - trailingRef.current.x) * 0.18;
      trailingRef.current.y += (posRef.current.y - trailingRef.current.y) * 0.18;

      setTrailingPos({ x: trailingRef.current.x, y: trailingRef.current.y });
      animFrameId.current = requestAnimationFrame(animateTrailing);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("mouseleave", handleMouseLeave);
    animFrameId.current = requestAnimationFrame(animateTrailing);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("mouseleave", handleMouseLeave);
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [isVisible]);

  // Remove old ripples after animation finishes
  useEffect(() => {
    if (ripples.length === 0) return;
    const timer = setTimeout(() => {
      setRipples((prev) => prev.slice(1));
    }, 600);
    return () => clearTimeout(timer);
  }, [ripples]);

  if (!isVisible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[9999] overflow-hidden">
      {/* Click Ripples */}
      {ripples.map((r) => (
        <span
          key={r.id}
          className="absolute rounded-full border border-lavender-300/60 bg-lavender-400/20 animate-ping pointer-events-none"
          style={{
            left: r.x - 20,
            top: r.y - 20,
            width: 40,
            height: 40,
            animationDuration: "0.6s",
          }}
        />
      ))}

      {/* Trailing Outer Ring Aura */}
      <div
        className={`absolute rounded-full transition-all duration-300 ease-out pointer-events-none backdrop-blur-[1px] ${
          isHovered
            ? "w-14 h-14 -translate-x-7 -translate-y-7 bg-lavender-400/15 border border-lavender-300/50 shadow-[0_0_25px_rgba(216,180,254,0.4)] scale-110"
            : isClicked
            ? "w-8 h-8 -translate-x-4 -translate-y-4 bg-white/30 border border-white/60 scale-90"
            : "w-10 h-10 -translate-x-5 -translate-y-5 bg-lavender-500/10 border border-lavender-300/30 shadow-[0_0_15px_rgba(184,165,254,0.2)]"
        }`}
        style={{
          transform: `translate3d(${trailingPos.x}px, ${trailingPos.y}px, 0) translate(-50%, -50%)`,
        }}
      />

      {/* Core Dot */}
      <div
        className={`absolute rounded-full transition-transform duration-100 ease-out pointer-events-none ${
          isHovered
            ? "w-2.5 h-2.5 bg-white shadow-[0_0_10px_#ffffff]"
            : "w-2 h-2 bg-gradient-to-r from-lavender-300 to-white shadow-[0_0_8px_rgba(216,180,254,0.8)]"
        }`}
        style={{
          transform: `translate3d(${position.x}px, ${position.y}px, 0) translate(-50%, -50%)`,
        }}
      />
    </div>
  );
}
