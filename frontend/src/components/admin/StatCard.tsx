/**
 * StatCard - Statistics display card with trend indicators
 * Displays key metrics with optional trend information
 */

"use client";

import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ 
  title, 
  value, 
  description, 
  trend, 
  icon,
  className 
}: StatCardProps) {
  return (
    <div 
      className={cn(
        "bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            {title}
          </p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white">
            {value}
          </p>
          {description && (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {description}
            </p>
          )}
        </div>
        
        {icon && (
          <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            {icon}
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-4 flex items-center gap-1.5">
          {trend.isPositive ? (
            <ArrowUpRight className="w-4 h-4 text-green-500" />
          ) : (
            <ArrowDownRight className={cn(
              "w-4 h-4",
              trend.value === 0 ? "text-slate-400" : "text-red-500"
            )} />
          )}
          <span className={cn(
            "text-sm font-medium",
            trend.isPositive 
              ? "text-green-600 dark:text-green-400" 
              : trend.value === 0
                ? "text-slate-400"
                : "text-red-600 dark:text-red-400"
          )}>
            {Math.abs(trend.value)}%
          </span>
          <span className="text-sm text-slate-400">
            vs last period
          </span>
        </div>
      )}
    </div>
  );
}

export default StatCard;
