import { forwardRef } from 'react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

export const Input = forwardRef(({ className, label, error, ...props }, ref) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={twMerge(clsx(
          'flex h-9 w-full rounded border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-950 focus:border-slate-950 transition-all duration-150 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-50',
          error && 'border-rose-500 focus:ring-rose-500 focus:border-rose-500',
          className
        ))}
        {...props}
      />
      {error && <p className="mt-1 text-[10px] text-rose-600 font-semibold uppercase tracking-wider">{error}</p>}
    </div>
  );
});

Input.displayName = 'Input';

