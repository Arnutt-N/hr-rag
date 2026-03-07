'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { ChatHistorySidebar } from '@/components/chat/ChatHistorySidebar';
import { ProjectManager } from '@/components/chat/ProjectManager';
import { useAuth } from '@/hooks/useAuth';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/auth/login');
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen grid place-items-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <AppShell
      title="Chats"
      sidebar={
        <div className="space-y-4">
          <ProjectManager />
          <ChatHistorySidebar />
        </div>
      }
    >
      <div className="h-[calc(100vh-140px)] overflow-hidden rounded-3xl border border-slate-200 bg-white/60 backdrop-blur dark:border-slate-800 dark:bg-slate-900/30">
        <ChatPanel />
      </div>
    </AppShell>
  );
}
