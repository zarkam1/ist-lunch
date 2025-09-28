import { useState, useEffect } from 'react';

interface AnimatedCounterProps {
  end: number;
  duration?: number;
  suffix?: string;
}

export default function AnimatedCounter({ end, duration = 1000, suffix = '' }: AnimatedCounterProps) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (end === 0) {
      setCurrent(0);
      return;
    }

    const stepTime = Math.abs(Math.floor(duration / end));
    const step = end / (duration / 16); // 60fps animation

    let current = 0;
    const timer = setInterval(() => {
      current += step;
      if (current >= end) {
        setCurrent(end);
        clearInterval(timer);
      } else {
        setCurrent(Math.floor(current));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [end, duration]);

  return (
    <span className="tabular-nums">
      {current.toLocaleString()}{suffix}
    </span>
  );
}