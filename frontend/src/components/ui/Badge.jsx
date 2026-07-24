import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

export const Badge = ({ className, variant = 'default', children, ...props }) => {
  const variants = {
    default: 'bg-slate-100 text-slate-800 border-slate-200/60',
    primary: 'bg-slate-900 text-white border-transparent',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200/80',
    warning: 'bg-amber-50 text-amber-800 border-amber-200/80',
    danger: 'bg-rose-50 text-rose-800 border-rose-200/80',
  };

  return (
    <span
      className={twMerge(clsx(
        'inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wider',
        variants[variant],
        className
      ))}
      {...props}
    >
      {children}
    </span>
  );
};

