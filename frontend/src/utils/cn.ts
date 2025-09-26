/**
 * 类名合并工具函数
 * 结合 clsx 和 tailwind-merge 提供智能的类名合并
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合并和优化 CSS 类名
 *
 * @param inputs - 类名输入（字符串、对象、数组等）
 * @returns 合并后的类名字符串
 *
 * @example
 * ```ts
 * cn('px-2 py-1', 'px-4') // 'py-1 px-4' (后面的 px-4 覆盖前面的 px-2)
 * cn('text-red-500', { 'text-blue-500': true }) // 'text-blue-500'
 * cn('flex', undefined, 'items-center') // 'flex items-center'
 * ```
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}