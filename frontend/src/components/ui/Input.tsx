"use client";

import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg",
          "bg-white dark:bg-gray-800 text-gray-900 dark:text-white",
          "placeholder:text-gray-400",
          "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";

export { Input };
