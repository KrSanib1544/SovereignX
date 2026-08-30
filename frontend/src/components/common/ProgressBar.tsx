// frontend/src/components/common/ProgressBar.tsx
import React from 'react';

interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  sublabel?: string;
  color?: 'cyan' | 'emerald' | 'amber' | 'rose';
  size?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  sublabel,
  color = 'cyan',
  size = 'md',
}) => {
  const clampedValue = Math.min(Math.max(value, 0), 100);

  const colorClasses = {
    cyan: 'bg-cyan-500 shadow-sm shadow-cyan-500/50',
    emerald: 'bg-emerald-500 shadow-sm shadow-emerald-500/50',
    amber: 'bg-amber-500 shadow-sm shadow-amber-500/50',
    rose: 'bg-rose-500 shadow-sm shadow-rose-500/50',
  };

  const heightClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className="w-full">
      {(label || sublabel) && (
        <div className="flex justify-between items-center mb-1 text-xs font-mono">
          {label && <span className="text-gray-400">{label}</span>}
          {sublabel && <span className="text-gray-300 font-medium">{sublabel}</span>}
        </div>
      )}
      <div className={`w-full bg-gray-800 rounded-full overflow-hidden ${heightClasses[size]}`}>
        <div
          className={`${colorClasses[color]} ${heightClasses[size]} rounded-full transition-all duration-300`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};
