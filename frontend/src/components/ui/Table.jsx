import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

export const Table = ({ className, children, ...props }) => (
  <div className="w-full overflow-auto border border-slate-200/80 rounded-lg bg-white shadow-[0_1px_3px_rgba(0,0,0,0.01),0_1px_2px_rgba(0,0,0,0.02)]">
    <table className={twMerge(clsx('w-full caption-bottom text-xs border-collapse', className))} {...props}>
      {children}
    </table>
  </div>
);

export const TableHeader = ({ className, children, ...props }) => (
  <thead className={twMerge(clsx('[&_tr]:border-b bg-slate-50 border-slate-200', className))} {...props}>
    {children}
  </thead>
);

export const TableBody = ({ className, children, ...props }) => (
  <tbody className={twMerge(clsx('[&_tr:last-child]:border-0', className))} {...props}>
    {children}
  </tbody>
);

export const TableRow = ({ className, children, ...props }) => (
  <tr className={twMerge(clsx('border-b border-slate-100 transition-colors hover:bg-slate-50/70', className))} {...props}>
    {children}
  </tr>
);

export const TableHead = ({ className, children, ...props }) => (
  <th className={twMerge(clsx('h-9 px-4 text-left align-middle font-semibold text-slate-500 uppercase tracking-wider text-[10px] [&:has([role=checkbox])]:pr-0', className))} {...props}>
    {children}
  </th>
);

export const TableCell = ({ className, children, ...props }) => (
  <td className={twMerge(clsx('px-4 py-3 align-middle text-slate-700 [&:has([role=checkbox])]:pr-0', className))} {...props}>
    {children}
  </td>
);

