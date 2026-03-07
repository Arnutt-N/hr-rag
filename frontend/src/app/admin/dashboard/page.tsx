"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Users,
  FolderOpen,
  FileText,
  MessageSquare,
  TrendingUp,
  Clock,
  Activity,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { adminApi } from "@/lib/admin-api";

interface Stats {
  total_users: number;
  total_members: number;
  total_projects: number;
  total_documents: number;
  total_chat_sessions: number;
  total_chat_messages: number;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await adminApi.analytics.overview(7);
        setStats(data.stats);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statCards = [
    {
      title: "Total Users",
      value: stats?.total_users || 0,
      icon: Users,
      color: "bg-blue-500",
      change: "+12%",
    },
    {
      title: "Members",
      value: stats?.total_members || 0,
      icon: Users,
      color: "bg-purple-500",
      change: "+5%",
    },
    {
      title: "Projects",
      value: stats?.total_projects || 0,
      icon: FolderOpen,
      color: "bg-green-500",
      change: "+8%",
    },
    {
      title: "Documents",
      value: stats?.total_documents || 0,
      icon: FileText,
      color: "bg-orange-500",
      change: "+15%",
    },
    {
      title: "Chat Sessions",
      value: stats?.total_chat_sessions || 0,
      icon: MessageSquare,
      color: "bg-pink-500",
      change: "+23%",
    },
    {
      title: "Messages",
      value: stats?.total_chat_messages || 0,
      icon: Activity,
      color: "bg-cyan-500",
      change: "+18%",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of your HR-RAG system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {stat.title}
                    </p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                      {loading ? (
                        <span className="animate-pulse">...</span>
                      ) : (
                        stat.value.toLocaleString()
                      )}
                    </p>
                    <div className="flex items-center gap-1 mt-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-green-500">{stat.change}</span>
                      <span className="text-sm text-gray-500"> vs last week</span>
                    </div>
                  </div>
                  <div
                    className={`${stat.color} p-3 rounded-xl bg-opacity-10`}
                  >
                    <Icon className={`w-6 h-6 ${stat.color.replace("bg-", "text-")}`} />
                  </div>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Manage Users", href: "/admin/users", icon: Users },
              { label: "View Analytics", href: "/admin/analytics", icon: TrendingUp },
              { label: "Content Moderation", href: "/admin/content", icon: FileText },
              { label: "System Settings", href: "/admin/settings", icon: Activity },
            ].map((action) => {
              const Icon = action.icon;
              return (
                <a
                  key={action.label}
                  href={action.href}
                  className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                >
                  <Icon className="w-5 h-5 text-primary-600" />
                  <span className="font-medium text-gray-900 dark:text-white">
                    {action.label}
                  </span>
                </a>
              );
            })}
          </div>
        </Card>
      </motion.div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Status
          </h2>
          <div className="space-y-4">
            {[
              { name: "API Server", status: "Operational", color: "green" },
              { name: "Database", status: "Operational", color: "green" },
              { name: "Vector Store", status: "Operational", color: "green" },
              { name: "LLM Providers", status: "Operational", color: "green" },
            ].map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between py-2"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full bg-${service.color}-500`}
                  />
                  <span className="text-gray-900 dark:text-white">{service.name}</span>
                </div>
                <span className="text-sm text-green-600 font-medium">
                  {service.status}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
