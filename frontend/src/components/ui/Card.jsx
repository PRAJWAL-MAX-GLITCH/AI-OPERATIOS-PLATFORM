import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

export const Card = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('bg-white rounded-lg border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.02),0_1px_2px_rgba(0,0,0,0.03)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.03)] transition-all duration-200', className))} {...props}>
      {children}
    </div>
  );
};

export const CardHeader = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('flex flex-col space-y-1 p-5 border-b border-slate-100', className))} {...props}>
      {children}
    </div>
  );
};

export const CardTitle = ({ className, children, ...props }) => {
  return (
    <h3 className={twMerge(clsx('text-sm font-semibold tracking-tight text-slate-800', className))} {...props}>
      {children}
    </h3>
  );
};

export const CardContent = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('p-5', className))} {...props}>
      {children}
    </div>
  );
};

