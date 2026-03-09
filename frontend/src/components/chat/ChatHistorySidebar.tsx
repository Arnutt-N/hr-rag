'use client';

import * as React from 'react';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn, truncateText, formatRelativeTime } from '@/lib/utils';
import { useChat } from '@/hooks/useChat';

export function ChatHistorySidebar() {
  const { sessions, currentSession, setCurrentSession, createSession } = useChat();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/60 p-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/30">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-sm font-semibold">Chat History</div>
        <Button size="sm" onClick={() => createSession()}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <div className="max-h-[40vh] space-y-2 overflow-y-auto pr-1">
        {sessions.length === 0 ? (
          <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500 dark:bg-slate-900/40">
            ยังไม่มีประวัติแชท
          </div>
        ) : (
          sessions.map((s) => {
            const active = currentSession === s.id;
            return (
              <button
                key={s.id}
                className={cn(
                  'w-full rounded-xl border p-3 text-left transition',
                  active
                    ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-slate-200 bg-white/60 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900/20 dark:hover:bg-slate-800/30'
                )}
                onClick={() => setCurrentSession(s.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <MessageSquare className="h-4 w-4 text-slate-500" />
                      <span className="truncate">{s.title || 'Chat'}</span>
                    </div>
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
