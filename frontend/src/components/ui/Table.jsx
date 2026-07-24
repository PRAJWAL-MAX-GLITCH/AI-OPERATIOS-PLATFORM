import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

export const Table = ({ className, children, ...props }) => (
  <div className="w-full overflow-auto border border-gray-200 rounded-lg bg-white">
    <table className={twMerge(clsx('w-full caption-bottom text-sm', className))} {...props}>
      {children}
    </table>
  </div>
);

export const TableHeader = ({ className, children, ...props }) => (
  <thead className={twMerge(clsx('[&_tr]:border-b bg-gray-50', className))} {...props}>
    {children}
  </thead>
);

export const TableBody = ({ className, children, ...props }) => (
  <tbody className={twMerge(clsx('[&_tr:last-child]:border-0', className))} {...props}>
    {children}
  </tbody>
);

export const TableRow = ({ className, children, ...props }) => (
  <tr className={twMerge(clsx('border-b border-gray-200 transition-colors hover:bg-gray-50/50 data-[state=selected]:bg-gray-50', className))} {...props}>
    {children}
  </tr>
);

export const TableHead = ({ className, children, ...props }) => (
  <th className={twMerge(clsx('h-10 px-4 text-left align-middle font-medium text-gray-500 [&:has([role=checkbox])]:pr-0', className))} {...props}>
    {children}
  </th>
);

export const TableCell = ({ className, children, ...props }) => (
  <td className={twMerge(clsx('p-4 align-middle [&:has([role=checkbox])]:pr-0', className))} {...props}>
    {children}
  </td>
);
