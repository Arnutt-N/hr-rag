'use client';

import * as React from 'react';
import { FolderPlus, Folder, Check } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useProjectStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { cn } from '@/lib/utils';

export function ProjectManager() {
  const { token } = useAuthStore();
  const { projects, currentProject, setProjects, setCurrentProject, addProject } = useProjectStore();
  const [name, setName] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    apiClient.setToken(token);
    const res = await apiClient.getProjects();
    if (res.success && res.data) setProjects(res.data);
    else setError(res.error || 'โหลดโปรเจกต์ไม่สำเร็จ');
    setLoading(false);
  }, [token, setProjects]);

  React.useEffect(() => {
    load();
  }, [load]);

  const create = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    apiClient.setToken(token);
    const res = await apiClient.createProject(name.trim());
    if (res.success && res.data) {
      addProject(res.data);
      setCurrentProject(res.data);
      setName('');
    } else setError(res.error || 'สร้างโปรเจกต์ไม่สำเร็จ');
    setLoading(false);
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/60 p-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/30">
      <div className="mb-2 text-sm font-semibold">Projects</div>

      <div className="flex gap-2">
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="ชื่อโปรเจกต์ใหม่" />
        <Button onClick={create} disabled={loading || !name.trim()}>
          <FolderPlus className="h-4 w-4" />
        </Button>
      </div>

      {error && <div className="mt-2 text-xs text-rose-600 dark:text-rose-300">{error}</div>}

      <div className="mt-3 space-y-2 max-h-[38vh] overflow-y-auto pr-1">
        {projects.length === 0 ? (
          <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500 dark:bg-slate-900/40">
            ยังไม่มีโปรเจกต์
          </div>
        ) : (
          projects.map((p) => {
            const active = currentProject?.id === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setCurrentProject(p)}
                className={cn(
                  'flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left transition',
                  active
                    ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-slate-200 bg-white/60 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900/20 dark:hover:bg-slate-800/30'
                )}
              >
                <div className="flex items-center gap-2">
                  <Folder className="h-4 w-4 text-slate-500" />
                  <div>
                    <div className="text-sm font-medium">{p.name}</div>
                    <div className="text-xs text-slate-500">Docs: {p.documentCount ?? 0}</div>
                  </div>
                </div>
                {active && <Check className="h-4 w-4 text-primary-600 dark:text-primary-400" />}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
