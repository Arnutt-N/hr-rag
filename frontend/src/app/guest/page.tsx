import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { Button } from '@/components/ui/Button';

export default function GuestPage() {
  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900">
      <div className="border-b border-slate-200 bg-white/60 p-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/30">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
              กลับ
            </Button>
          </Link>
          <div className="text-sm font-semibold">Guest Chat (ไม่บันทึกประวัติ)</div>
          <div className="w-20" />
        </div>
      </div>
      <div className="h-[calc(100vh-56px)]">
        <ChatPanel message={{ id: "", role: "assistant", content: "", timestamp: new Date() }} />
      </div>
    </div>
  );
}
