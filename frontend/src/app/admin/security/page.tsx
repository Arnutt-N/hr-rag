"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Shield, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

interface LoginAttempt {
  id: number;
  username: string;
  success: boolean;
  ip_address?: string;
  timestamp: string;
}

export default function AdminSecurity() {
  const [attempts, setAttempts] = useState<LoginAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "success" | "failed">("all");

  useEffect(() => {
    fetchAttempts();
  }, [filter]);

  const fetchAttempts = async () => {
    const token = localStorage.getItem("token");
    try {
      const queryParams = filter !== "all" ? `?success=${filter === "success"}` : "";
      const res = await fetch(
        `http://localhost:8000/admin/security/login-attempts${queryParams}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setAttempts(data.items);
      }
    } catch (error) {
      console.error("Failed to fetch login attempts:", error);
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

  const failedAttempts = attempts.filter((a) => !a.success).length;
  const successAttempts = attempts.filter((a) => a.success).length;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Security</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitor login attempts and security events
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-xl mr-4">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Attempts</p>
              <p className="text-2xl font-bold">{attempts.length}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-xl mr-4">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Successful</p>
              <p className="text-2xl font-bold">{successAttempts}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-red-100 dark:bg-red-900 rounded-xl mr-4">
              <XCircle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Failed</p>
              <p className="text-2xl font-bold">{failedAttempts}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-4 mb-6">
        <div className="flex gap-4">
          {["all", "success", "failed"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f as any)}
              className={`px-4 py-2 rounded-lg capitalize ${
                filter === f
                  ? "bg-primary-600 text-white"
                  : "bg-gray-100 dark:bg-gray-800 hover:bg-gray-200"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </Card>

      {/* Login Attempts */}
      <Card className="overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Username</th>
              <th className="px-6 py-3 text-left">IP Address</th>
              <th className="px-6 py-3 text-left">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {attempts.map((attempt) => (
              <tr
                key={attempt.id}
                className={
                  attempt.success ? "" : "bg-red-50 dark:bg-red-900/10"
                }
              >
                <td className="px-6 py-4">
                  {attempt.success ? (
                    <span className="flex items-center text-green-600">
                      <CheckCircle className="w-4 h-4 mr-1" /
                      Success
                    </span>
                  ) : (
                    <span className="flex items-center text-red-600">
                      <XCircle className="w-4 h-4 mr-1" /
                      Failed
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 font-medium">{attempt.username}</td>
                <td className="px-6 py-4">{attempt.ip_address || "-"}</td>
                <td className="px-6 py-4">
                  {new Date(attempt.timestamp).toLocaleString("th-TH")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
