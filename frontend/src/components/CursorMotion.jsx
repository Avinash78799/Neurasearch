import { useEffect, useState, useRef } from "react";

export default function CursorMotion() {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [isVisible, setIsVisible] = useState(false);
  const posRef = useRef({ x: -100, y: -100 });

  useEffect(() => {
    if (typeof window === "undefined" || "ontouchstart" in window) return;

    const handleMouseMove = (e) => {
      if (!isVisible) setIsVisible(true);
      posRef.current = { x: e.clientX, y: e.clientY };
      setPosition({ x: e.clientX, y: e.clientY });
    };

    const handleMouseLeave = () => setIsVisible(false);

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    document.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div
      className="fixed pointer-events-none z-50 transition-opacity duration-300"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: "translate(-50%, -50%)",
      }}
    >
      {/* Ultra-subtle ambient glow, zero obstruction */}
      <div className="w-8 h-8 rounded-full bg-lavender-400/10 blur-md pointer-events-none" />
    </div>
  );
}
