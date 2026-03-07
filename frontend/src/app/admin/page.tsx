"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  FolderOpen,
  FileText,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Activity,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface SystemStats {
  total_users: number;
  total_members: number;
  total_projects: number;
  total_documents: number;
  total_chat_sessions: number;
  total_chat_messages: number;
}

interface DailyStat {
  date: string;
  queries: number;
  sessions: number;
  new_users: number;
  new_documents: number;
}

interface TopUser {
  user_id: number;
  username: string;
  email: string;
  message_count: number;
}

interface TopProvider {
  provider: string;
  count: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStat[]>([]);
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [topProviders, setTopProviders] = useState<TopProvider[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("http://localhost:8000/admin/analytics?days=7", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data.stats);
        setDailyStats(data.daily_stats);
        setTopUsers(data.top_active_users);
        setTopProviders(data.top_llm_providers);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Users",
      value: stats?.total_users || 0,
      icon: Users,
      color: "blue",
    },
    {
      title: "Projects",
      value: stats?.total_projects || 0,
      icon: FolderOpen,
      color: "green",
    },
    {
      title: "Documents",
      value: stats?.total_documents || 0,
      icon: FileText,
      color: "purple",
    },
    {
      title: "Chat Messages",
      value: stats?.total_chat_messages || 0,
      icon: MessageSquare,
      color: "orange",
    },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          System overview and key metrics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                    <p className="text-3xl font-bold">{card.value.toLocaleString()}</p>
                  </div>
                  <div className={`p-3 bg-${card.color}-100 dark:bg-${card.color}-900 rounded-xl`}>
                    <Icon className={`w-6 h-6 text-${card.color}-600`} />
                  </div>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Daily Activity */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Daily Activity (Last 7 Days)</h2>
          <div className="space-y-4">
            {dailyStats.slice(-7).map((day) => (
              <div key={day.date} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {new Date(day.date).toLocaleDateString("th-TH", {
                    month: "short",
                    day: "numeric",
                  })}
                </span>
                <div className="flex gap-4">
                  <span className="text-sm" title="Queries">
                    <MessageSquare className="w-4 h-4 inline mr-1" /
                    {day.queries}
                  </span>
                  <span className="text-sm" title="New Users">
                    <Users className="w-4 h-4 inline mr-1" /
                    {day.new_users}
                  </span>
                  <span className="text-sm" title="New Documents">
                    <FileText className="w-4 h-4 inline mr-1" /
                    {day.new_documents}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top LLM Providers */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Top LLM Providers</h2>
          <div className="space-y-4">
            {topProviders.map((provider, index) => (
              <div key={provider.provider} className="flex items-center">
                <span className="w-8 text-gray-500">#{index + 1}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium capitalize">{provider.provider}</span>
                    <span className="text-sm text-gray-500">
                      {provider.count.toLocaleString()} uses
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full"
                      style={{
                        width: `${(provider.count / topProviders[0].count) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Active Users */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Top Active Users</h2>
          <div className="space-y-3">
            {topUsers.slice(0, 5).map((user, index) => (
              <div
                key={user.user_id}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mr-3">
                    <span className="text-primary-600 font-semibold">{index + 1}</span>
                  </div>
                  <div>
                    <p className="font-medium">{user.username || user.email}</p>
                    <p className="text-sm text-gray-500">{user.email}</p>
                  </div>
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <MessageSquare className="w-4 h-4 mr-1" /
                  {user.message_count.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Quick Actions */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <a
              href="/admin/users"
              className="block p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center">
                <Users className="w-5 h-5 text-primary-600 mr-3" /
                <div>
                  <p className="font-medium">Manage Users</p>
                  <p className="text-sm text-gray-500">View and manage user accounts</p>
                </div>
              </div>
            </a>
            <a
              href="/admin/analytics"
              className="block p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center">
                <Activity className="w-5 h-5 text-green-600 mr-3" /
                <div>
                  <p className="font-medium">View Analytics</p>
                  <p className="text-sm text-gray-500">Detailed system statistics</p>
                </div>
              </div>
            </a>
            <a
              href="/admin/settings"
              className="block p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center">
                <TrendingUp className="w-5 h-5 text-purple-600 mr-3" /
                <div>
                  <p className="font-medium">System Settings</p>
                  <p className="text-sm text-gray-500">Configure system parameters</p>
                </div>
              </div>
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
}
