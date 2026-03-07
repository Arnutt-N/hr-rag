/**
 * SearchBar - Advanced search with filters
 * Generic search component for admin lists with filter chips
 */

"use client";

import { useMemo, useState } from "react";
import { Search, X, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

export type FilterType = "select" | "text" | "date" | "boolean";

export interface SearchFilterOption {
  label: string;
  value: string;
}

export interface SearchFilterDef {
  key: string;
  label: string;
  type: FilterType;
  options?: SearchFilterOption[]; // for select
  placeholder?: string;
}

export type SearchFilterValues = Record<string, string | boolean | undefined>;

interface SearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  filters?: SearchFilterDef[];
  values?: SearchFilterValues;
  onValuesChange?: (values: SearchFilterValues) => void;
  placeholder?: string;
  className?: string;
}

export function SearchBar({
  query,
  onQueryChange,
  filters = [],
  values = {},
  onValuesChange,
  placeholder = "Search...",
  className,
}: SearchBarProps) {
  const [showFilters, setShowFilters] = useState(false);

  const activeFilterCount = useMemo(() => {
    return filters.reduce((count, f) => {
      const v = values[f.key];
      if (v === undefined) return count;
      if (typeof v === "string" && v.trim() === "") return count;
      return count + 1;
    }, 0);
  }, [filters, values]);

  const setValue = (key: string, value: string | boolean | undefined) => {
    const next = { ...values, [key]: value };
    if (value === undefined || value === "") delete next[key];
    onValuesChange?.(next);
  };

  const clearAll = () => {
    onQueryChange("");
    onValuesChange?.({});
  };

  return (
    <div className={cn("bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4", className)}>
      <div className="flex flex-wrap items-center gap-3">
        {/* Search input */}
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder={placeholder}
            className="pl-10 pr-10"
          />
          {query && (
            <button
              onClick={() => onQueryChange("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Filter toggle */}
        {filters.length > 0 && (
          <Button
            variant={showFilters ? "primary" : "outline"}
            onClick={() => setShowFilters((s) => !s)}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filters{activeFilterCount ? ` (${activeFilterCount})` : ""}
          </Button>
        )}

        <Button variant="outline" onClick={clearAll}>
          Clear
        </Button>
      </div>

      {/* Active filter chips */}
      {(query || activeFilterCount > 0) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {query && (
            <span className="text-xs px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
              Query: <span className="font-medium">{query}</span>
            </span>
          )}
          {filters.map((f) => {
            const v = values[f.key];
            if (v === undefined || (typeof v === "string" && v.trim() === "")) return null;

            let display = String(v);
            if (f.type === "select" && f.options) {
              display = f.options.find((o) => o.value === v)?.label ?? String(v);
            }
            if (f.type === "boolean") {
              display = v ? "Yes" : "No";
            }

            return (
              <button
                key={f.key}
                onClick={() => setValue(f.key, undefined)}
                className="text-xs px-2 py-1 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
                title="Click to remove"
              >
                {f.label}: <span className="font-medium">{display}</span> <span className="opacity-70">×</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Filters panel */}
      {showFilters && filters.length > 0 && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filters.map((f) => {
            const v = values[f.key];

            if (f.type === "select") {
              return (
                <label key={f.key} className="text-sm">
                  <div className="mb-1 text-slate-600 dark:text-slate-300 font-medium">{f.label}</div>
                  <select
                    value={(typeof v === "string" ? v : "") || ""}
                    onChange={(e) => setValue(f.key, e.target.value || undefined)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
                  >
                    <option value="">All</option>
                    {(f.options || []).map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
              );
            }

            if (f.type === "boolean") {
              return (
                <label key={f.key} className="text-sm">
                  <div className="mb-1 text-slate-600 dark:text-slate-300 font-medium">{f.label}</div>
                  <select
                    value={v === undefined ? "" : v ? "true" : "false"}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === "") return setValue(f.key, undefined);
                      setValue(f.key, val === "true");
                    }}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
                  >
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </label>
              );
            }

            return (
              <label key={f.key} className="text-sm">
                <div className="mb-1 text-slate-600 dark:text-slate-300 font-medium">{f.label}</div>
                <Input
                  type={f.type === "date" ? "date" : "text"}
                  value={(typeof v === "string" ? v : "") || ""}
                  onChange={(e) => setValue(f.key, e.target.value || undefined)}
                  placeholder={f.placeholder}
                />
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default SearchBar;
