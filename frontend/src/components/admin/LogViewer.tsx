/**
 * LogViewer - System logs display with filtering
 * Displays system logs with search, filtering, and severity levels
 */

"use client";

import { useState, useMemo } from "react";
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Download,
  AlertTriangle,
  Info,
  XCircle,
  Bug
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type LogLevel = "all" | "error" | "warning" | "info" | "debug";

interface LogEntry {
  id: string;
  timestamp: string;
  level: "error" | "warning" | "info" | "debug";
  message: string;
  source?: string;
  user_id?: number;
  details?: Record<string, unknown>;
}

interface LogViewerProps {
  logs: LogEntry[];
  onRefresh?: () => void;
  onExport?: (logs: LogEntry[]) => void;
  isLoading?: boolean;
  className?: string;
}

const levelConfig = {
  error: { 
    icon: XCircle, 
    color: "text-red-500", 
    bg: "bg-red-50 dark:bg-red-900/20",
    border: "border-red-200 dark:border-red-800",
    label: "Error"
  },
  warning: { 
    icon: AlertTriangle, 
    color: "text-amber-500", 
    bg: "bg-amber-50 dark:bg-amber-900/20",
    border: "border-amber-200 dark:border-amber-800",
    label: "Warning"
  },
  info: { 
    icon: Info, 
    color: "text-blue-500", 
    bg: "bg-blue-50 dark:bg-blue-900/20",
    border: "border-blue-200 dark:border-blue-800",
    label: "Info"
  },
  debug: { 
    icon: Bug, 
    color: "text-slate-500", 
    bg: "bg-slate-50 dark:bg-slate-900/20",
    border: "border-slate-200 dark:border-slate-800",
    label: "Debug"
  },
};

export function LogViewer({
  logs,
  onRefresh,
  onExport,
  isLoading = false,
  className
}: LogViewerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState<LogLevel>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  // Get unique sources
  const sources = useMemo(() => {
    const uniqueSources = new Set(logs.map(log => log.source).filter(Boolean));
    return Array.from(uniqueSources);
  }, [logs]);

  // Filter logs
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch = 
          log.message.toLowerCase().includes(query) ||
          log.source?.toLowerCase().includes(query) ||
          log.id.toLowerCase().includes(query);
        if (!matchesSearch) return false;
      }

      // Level filter
      if (levelFilter !== "all" && log.level !== levelFilter) {
        return false;
      }

      // Source filter
      if (sourceFilter !== "all" && log.source !== sourceFilter) {
        return false;
      }

      return true;
    });
  }, [logs, searchQuery, levelFilter, sourceFilter]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    });
  };

  const handleExport = () => {
    if (onExport) {
      onExport(filteredLogs);
    } else {
      const blob = new Blob([JSON.stringify(filteredLogs, null, 2)], { 
        type: "application/json" 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `system-logs-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className={cn("bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700", className)}>
      {/* Toolbar */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Level Filter */}
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value as LogLevel)}
          className="px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
        >
          <option value="all">All Levels</option>
          <option value="error">Errors</option>
          <option value="warning">Warnings</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>

        {/* Source Filter */}
        {sources.length > 0 && (
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
          >
            <option value="all">All Sources</option>
            {sources.map(source => (
              <option key={source} value={source}>{source}</option>
            ))}
          </select>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant={autoRefresh ? "primary" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4" />
          </Button>
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh}>
              Refresh
            </Button>
          )}
        </div>
      </div>

      {/* Log Count */}
      <div className="px-4 py-2 bg-slate-50 dark:bg-slate-900/50 text-sm text-slate-500 border-b border-slate-200 dark:border-slate-700">
        Showing {filteredLogs.length} of {logs.length} logs
      </div>

      {/* Log List */}
      <div className="max-h-[500px] overflow-y-auto">
        {filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Filter className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No logs found matching your filters</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-200 dark:divide-slate-700">
            {filteredLogs.map((log) => {
              const config = levelConfig[log.level];
              const Icon = config.icon;
              const isExpanded = expandedLog === log.id;

              return (
                <div
                  key={log.id}
                  className={cn(
                    "p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors cursor-pointer",
                    config.bg,
                    config.border
                  )}
                  onClick={() => setExpandedLog(isExpanded ? null : log.id)}
                >
                  <div className="flex items-start gap-3">
                    <Icon className={cn("w-5 h-5 flex-shrink-0 mt-0.5", config.color)} />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={cn("text-xs font-medium px-2 py-0.5 rounded", config.bg, config.color)}>
                          {config.label}
                        </span>
                        <span className="text-xs text-slate-500">
                          {formatTimestamp(log.timestamp)}
                        </span>
                        {log.source && (
                          <span className="text-xs text-slate-400">
                            [{log.source}]
                          </span>
                        )}
                        {log.user_id && (
                          <span className="text-xs text-slate-400">
                            User: {log.user_id}
                          </span>
                        )}
                      </div>
                      
                      <p className="mt-1 text-sm text-slate-700 dark:text-slate-300 font-mono">
                        {log.message}
                      </p>

                      {isExpanded && log.details && (
                        <pre className="mt-2 p-2 bg-slate-900 text-slate-100 rounded text-xs overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default LogViewer;
