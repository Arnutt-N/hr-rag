'use client';

import * as React from 'react';
import { Menu, LogOut, Settings, Folder, MessageSquare, Home } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { useUIStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

function NavItem({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  const pathname = usePathname();
  const active = pathname === href;
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition',
        active
          ? 'bg-primary-600 text-white shadow-sm'
          : 'text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800'
      )}
    >
      <span className="h-4 w-4">{icon}</span>
      {label}
    </Link>
  );
}

export function AppShell({
  sidebar,
  children,
  title,
}: {
  sidebar?: React.ReactNode;
  children: React.ReactNode;
  title?: string;
}) {
  const { logout, user } = useAuth();
  const { mobileMenuOpen, toggleMobileMenu, closeMobileMenu } = useUIStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900">
      <div className="mx-auto flex min-h-screen max-w-7xl">
        {/* Desktop Sidebar */}
        <aside className="hidden w-80 border-r border-slate-200 bg-white/60 p-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/30 lg:block">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-bold">HR-RAG</div>
              <div className="text-xs text-slate-500">Dashboard</div>
            </div>
            <ThemeToggle />
          </div>

          <div className="mt-6 space-y-2">
            <NavItem href="/dashboard" icon={<Home className="h-4 w-4" />} label="Overview" />
            <NavItem href="/dashboard" icon={<MessageSquare className="h-4 w-4" />} label="Chats" />
            <NavItem href="/dashboard/projects" icon={<Folder className="h-4 w-4" />} label="Projects" />
            <NavItem href="/settings" icon={<Settings className="h-4 w-4" />} label="Settings" />
          </div>

          <div className="mt-6 rounded-2xl border border-slate-200 bg-white/70 p-4 dark:border-slate-800 dark:bg-slate-900/40">
            <div className="text-sm font-semibold">Signed in</div>
            <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">{user?.name}</div>
            <div className="text-xs text-slate-500">{user?.email}</div>
            <Button variant="secondary" className="mt-3 w-full" onClick={logout}>
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>

          {sidebar && <div className="mt-6">{sidebar}</div>}
        </aside>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="sidebar-mobile lg:hidden">
            <div className="flex items-center justify-between border-b border-slate-200 p-4 dark:border-slate-800">
              <div className="text-lg font-bold">HR-RAG</div>
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <Button variant="ghost" size="sm" onClick={closeMobileMenu}>
                  Close
                </Button>
              </div>
            </div>
            <div className="p-4 space-y-2">
              <NavItem href="/dashboard" icon={<Home className="h-4 w-4" />} label="Overview" />
              <NavItem href="/dashboard/projects" icon={<Folder className="h-4 w-4" />} label="Projects" />
              <NavItem href="/settings" icon={<Settings className="h-4 w-4" />} label="Settings" />
              <Button variant="secondary" className="mt-3 w-full" onClick={logout}>
                <LogOut className="h-4 w-4" />
                Logout
              </Button>
            </div>
          </div>
        )}

        <main className="flex-1">
          {/* Top bar */}
          <div className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/60 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/30 lg:px-6">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" className="lg:hidden" onClick={toggleMobileMenu}>
                <Menu className="h-5 w-5" />
              </Button>
              <div>
                <div className="text-sm font-semibold">{title || 'Dashboard'}</div>
                <div className="text-xs text-slate-500">HR knowledge assistant</div>
              </div>
            </div>
            <div className="hidden lg:block">
              <ThemeToggle />
            </div>
          </div>

          <div className="p-4 lg:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
