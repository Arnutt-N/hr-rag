"use client";

import { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("theme");
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    setIsDark(saved === "dark" || (!saved && prefersDark));
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (isDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark, mounted]);

  if (!mounted) return null;

  return (
    <button
      onClick={() => setIsDark(!isDark)}
      className={cn(
        "p-2 rounded-lg transition-colors",
        "hover:bg-gray-100 dark:hover:bg-gray-800",
        className
      )}
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-yellow-500" />
      ) : (
        <Moon className="w-5 h-5 text-gray-600" />
      )}
    </button>
  );
}
