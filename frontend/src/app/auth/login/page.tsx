'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { login, error } = useAuth();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const ok = await login({ email, password });
    setLoading(false);
    if (ok) router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50 px-4 py-10 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900">
      <div className="mx-auto max-w-md">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="gradient-border">
            <CardHeader>
              <CardTitle>เข้าสู่ระบบ</CardTitle>
              <div className="text-sm text-slate-500">ยินดีต้อนรับกลับมา</div>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="space-y-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <Input className="pl-9" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <Input className="pl-9" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
                  </div>
                </div>

                {error && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/40 dark:bg-rose-950/30 dark:text-rose-200">
                    {error}
                  </div>
                )}

                <Button className="w-full" disabled={loading || !email || !password}>
                  {loading ? 'กำลังเข้าสู่ระบบ...' : 'Login'}
                  <ArrowRight className="h-4 w-4" />
                </Button>

                <div className="text-center text-sm text-slate-600 dark:text-slate-300">
                  ยังไม่มีบัญชี?{' '}
                  <Link className="font-semibold text-primary-600 hover:underline" href="/auth/register">
                    Register
                  </Link>
                </div>

                <div className="text-center text-xs text-slate-500">
                  หรือทดลองแบบ <Link className="text-primary-600 hover:underline" href="/guest">Guest</Link>
                </div>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
