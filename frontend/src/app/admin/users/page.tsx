"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  MoreHorizontal,
  UserCheck,
  UserX,
  Key,
  Eye,
  ChevronLeft,
  ChevronRight,
  Download,
  Shield,
  User,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { adminApi } from "@/lib/admin-api";

interface UserItem {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_member: boolean;
  is_active: boolean;
  created_at: string;
  projects_count: number;
  chat_sessions_count: number;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [showResetModal, setShowResetModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserItem | null>(null);
  const [newPassword, setNewPassword] = useState("");

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await adminApi.users.list({
        page,
        page_size: 20,
        search: search || undefined,
      });
      setUsers(data.items);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error("Failed to fetch users:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, search]);

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await adminApi.users.toggleStatus(userId, !currentStatus);
      fetchUsers();
    } catch (error) {
      console.error("Failed to toggle status:", error);
    }
  };

  const handleResetPassword = async () => {
    if (!selectedUser || !newPassword) return;
    try {
      await adminApi.users.resetPassword(selectedUser.id, newPassword);
      setShowResetModal(false);
      setNewPassword("");
      setSelectedUser(null);
    } catch (error) {
      console.error("Failed to reset password:", error);
    }
  };

  const handleExport = async () => {
    try {
      const data = await adminApi.export.users();
      const blob = new Blob([data.csv], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `users-${new Date().toISOString().split("T")[0]}.csv`;
      a.click();
    } catch (error) {
      console.error("Failed to export users:", error);
    }
  };

  const toggleSelectAll = () => {
    if (selectedUsers.length === users.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users.map((u) => u.id));
    }
  };

  const toggleSelectUser = (userId: number) => {
    if (selectedUsers.includes(userId)) {
      setSelectedUsers(selectedUsers.filter((id) => id !== userId));
    } else {
      setSelectedUsers([...selectedUsers, userId]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            User Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage users, roles, and permissions
          </p>
        </div>
        <Button onClick={handleExport} variant="outline" className="gap-2">
          <Download className="w-4 h-4" />
          Export CSV
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter className="w-4 h-4" />
            Filters
          </Button>
        </div>
      </Card>

      {/* Bulk Actions */}
      {selectedUsers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-primary-50 dark:bg-primary-900/20 p-4 rounded-lg flex items-center gap-4"
        >
          <span className="text-sm font-medium text-primary-900 dark:text-primary-100">
            {selectedUsers.length} users selected
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline">Enable</Button>
            <Button size="sm" variant="outline">Disable</Button>
            <Button size="sm" variant="destructive">Delete</Button>
          </div>
        </motion.div>
      )}

      {/* Users Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedUsers.length === users.length && users.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  User
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Role
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Projects
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Chats
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Created
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr
                    key={user.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedUsers.includes(user.id)}
                        onChange={() => toggleSelectUser(user.id)}
                        className="rounded border-gray-300"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                          <User className="w-4 h-4 text-primary-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {user.username}
                          </p>
                          <p className="text-sm text-gray-500">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {user.role === "admin" && (
                          <Shield className="w-4 h-4 text-purple-500" />
                        )}
                        <span
                          className={`text-sm capitalize ${
                            user.role === "admin"
                              ? "text-purple-600 font-medium"
                              : user.is_member
                              ? "text-blue-600"
                              : "text-gray-600"
                          }`}
                        >
                          {user.role}
                          {user.is_member && user.role !== "admin" && " (Member)"}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                          user.is_active
                            ? "bg-green-100 text-green-700 dark:bg-green-900/20"
                            : "bg-red-100 text-red-700 dark:bg-red-900/20"
                        }`}
                      >
                        {user.is_active ? (
                          <>
                            <UserCheck className="w-3 h-3" /> Active
                          </>
                        ) : (
                          <>
                            <UserX className="w-3 h-3" /> Inactive
                          </>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-900 dark:text-white">
                      {user.projects_count}
                    </td>
                    <td className="px-4 py-3 text-gray-900 dark:text-white">
                      {user.chat_sessions_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <a
                          href={`/admin/users/${user.id}`}
                          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4 text-gray-600" />
                        </a>
                        <button
                          onClick={() => {
                            setSelectedUser(user);
                            setShowResetModal(true);
                          }}
                          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                          title="Reset Password"
                        >
                          <Key className="w-4 h-4 text-gray-600" />
                        </button>
                        <button
                          onClick={() => handleToggleStatus(user.id, user.is_active)}
                          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                          title={user.is_active ? "Disable" : "Enable"}
                        >
                          {user.is_active ? (
                            <UserX className="w-4 h-4 text-red-600" />
                          ) : (
                            <UserCheck className="w-4 h-4 text-green-600" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </Card>

      {/* Reset Password Modal */}
      {showResetModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md m-4"
          >
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Reset Password
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Reset password for {selectedUser.username}
            </p>
            <Input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mb-4"
            />
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShowResetModal(false);
                  setNewPassword("");
                  setSelectedUser(null);
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleResetPassword} disabled={!newPassword}>
                Reset Password
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
