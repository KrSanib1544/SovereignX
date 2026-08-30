// frontend/src/components/common/Badge.tsx
import React from 'react';

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'accent' | 'outline';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  children,
  className = '',
}) => {
  const baseClasses = 'inline-flex items-center font-mono font-medium rounded-full transition-colors';
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };

  const variantClasses = {
    default: 'bg-gray-800 text-gray-300 border border-gray-700',
    success: 'bg-emerald-950/80 text-emerald-400 border border-emerald-600/40 shadow-sm shadow-emerald-900/20',
    warning: 'bg-amber-950/80 text-amber-400 border border-amber-600/40 shadow-sm shadow-amber-900/20',
    danger: 'bg-rose-950/80 text-rose-400 border border-rose-600/40 shadow-sm shadow-rose-900/20',
    accent: 'bg-cyan-950/80 text-cyan-400 border border-cyan-600/40 shadow-sm shadow-cyan-900/20',
    outline: 'bg-transparent text-gray-400 border border-gray-700',
  };

  return (
    <span className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};
