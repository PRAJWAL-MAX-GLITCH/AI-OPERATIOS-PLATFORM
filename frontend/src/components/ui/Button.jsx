import { forwardRef } from 'react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

export const Button = forwardRef(({ 
  className, 
  variant = 'primary', 
  size = 'md', 
  isLoading, 
  children, 
  disabled,
  ...props 
}, ref) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-md text-xs font-semibold tracking-wide uppercase transition-all duration-200 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 select-none';
  
  const variants = {
    primary: 'bg-slate-900 text-white hover:bg-slate-800 active:bg-black border border-slate-950/20 shadow-[0_1px_2px_rgba(0,0,0,0.08)]',
    secondary: 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:text-slate-950 active:bg-slate-100 shadow-[0_1px_2px_rgba(0,0,0,0.02)]',
    danger: 'bg-red-600 text-white hover:bg-red-500 active:bg-red-700 border border-red-700/20 shadow-[0_1px_2px_rgba(0,0,0,0.08)]',
    ghost: 'hover:bg-slate-100 hover:text-slate-900 text-slate-500',
  };

  const sizes = {
    sm: 'h-8 px-3 rounded',
    md: 'h-9 px-4 rounded-md',
    lg: 'h-10 px-5 rounded-md text-sm',
  };

  return (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      {...props}
    >
      {isLoading && <Loader2 className="mr-1.5 h-3 w-3 animate-spin text-current" />}
      {children}
    </button>
  );
});

Button.displayName = 'Button';

