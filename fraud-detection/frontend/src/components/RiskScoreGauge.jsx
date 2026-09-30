import React from 'react';

export default function RiskScoreGauge({ score = 0, level = "LOW", size = 160 }) {
  const radius = 54;
  const strokeWidth = 10;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;

  let strokeColor = "#10B981"; // Emerald
  let glowColor = "rgba(16, 185, 129, 0.25)";
  let textColor = "text-emerald-400";

  if (score >= 70 || level === "HIGH") {
    strokeColor = "#EF4444"; // Red
    glowColor = "rgba(239, 68, 68, 0.3)";
    textColor = "text-red-400";
  } else if (score >= 30 || level === "MEDIUM") {
    strokeColor = "#F59E0B"; // Amber
    glowColor = "rgba(245, 158, 11, 0.25)";
    textColor = "text-amber-400";
  }

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        height={size}
        width={size}
        className="transform -rotate-90 transition-all duration-700 ease-out"
        style={{ filter: `drop-shadow(0 0 12px ${glowColor})` }}
      >
        {/* Background track circle */}
        <circle
          stroke="#1E293B"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={normalizedRadius}
          cx={size / 2}
          cy={size / 2}
        />
        {/* Animated progress circle */}
        <circle
          stroke={strokeColor}
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={`${circumference} ${circumference}`}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={size / 2}
          cy={size / 2}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className={`text-4xl font-extrabold tracking-tight ${textColor}`}>
          {score}
        </span>
        <span className="text-[11px] font-medium uppercase tracking-widest text-slate-400">
          / 100 Score
        </span>
        <span className={`mt-0.5 text-xs font-bold uppercase tracking-wider ${textColor}`}>
          {level} RISK
        </span>
      </div>
    </div>
  );
}
