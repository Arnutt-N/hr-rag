/**
 * AdminSidebar - Navigation sidebar for admin pages
 * Provides navigation links to different admin sections
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Settings, 
  BarChart3, 
  Shield,
  Activity,
  LogOut
} from "lucide-react";

interface AdminSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/activity", label: "Activity", icon: Activity },
  { href: "/admin/usage", label: "Usage Stats", icon: BarChart3 },
  { href: "/admin/logs", label: "System Logs", icon: FileText },
  { href: "/admin/security", label: "Security", icon: Shield },
  { href: "/admin/settings", label: "Settings", icon: Settings },
];

export function AdminSidebar({ isOpen = true, onClose }: AdminSidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && onClose && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`
          fixed top-0 left-0 z-50 h-full w-64 bg-slate-900 text-white
          transform transition-transform duration-200 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:z-auto
          flex flex-col
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <Link href="/admin" className="text-xl font-bold text-blue-400">
            HR-RAG Admin
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== "/admin" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg
                  transition-colors duration-150
                  ${isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg
              text-slate-400 hover:bg-slate-800 hover:text-white
              transition-colors duration-150"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Back to App</span>
          </Link>
        </div>
      </aside>
    </>
  );
}

export default AdminSidebar;
