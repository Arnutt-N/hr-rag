'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { ProjectManager } from '@/components/chat/ProjectManager';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

export default function ProjectsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/auth/login');
  }, [isLoading, isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <AppShell title="Projects" sidebar={<ProjectManager />}>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>จัดการโปรเจกต์</CardTitle>
            <div className="text-sm text-slate-500">สร้าง/เลือกโปรเจกต์สำหรับแยกชุดเอกสาร</div>
          </CardHeader>
          <CardContent>
            <ProjectManager />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>แนวทางแนะนำ</CardTitle>
            <div className="text-sm text-slate-500">ทำให้ RAG ตอบได้แม่นขึ้น</div>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-5 text-sm text-slate-600 dark:text-slate-300">
              <li>แยกโปรเจกต์ตามฝ่าย/ปี/ประเภทนโยบาย (เช่น HR Policies 2025)</li>
              <li>อัปโหลดเอกสาร PDF/DOCX ที่เป็นแหล่งข้อมูลจริง</li>
              <li>ตั้งชื่อโปรเจกต์ให้สื่อความหมายเพื่อค้นหาได้ง่าย</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
