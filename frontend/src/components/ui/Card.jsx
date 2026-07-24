import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

export const Card = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('bg-white rounded-lg border border-gray-200 shadow-sm', className))} {...props}>
      {children}
    </div>
  );
};

export const CardHeader = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('flex flex-col space-y-1.5 p-6', className))} {...props}>
      {children}
    </div>
  );
};

export const CardTitle = ({ className, children, ...props }) => {
  return (
    <h3 className={twMerge(clsx('text-lg font-semibold leading-none tracking-tight', className))} {...props}>
      {children}
    </h3>
  );
};

export const CardContent = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('p-6 pt-0', className))} {...props}>
      {children}
    </div>
  );
};
