/**
 * UserRow - User list item with actions
 * Displays user information with admin action buttons
 */

"use client";

import { 
  User, 
  Mail, 
  Shield, 
  MoreVertical,
  Edit,
  Trash2,
  Ban,
  CheckCircle,
  XCircle
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "../ui/Button";

interface UserData {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: "admin" | "member" | "user";
  is_active: boolean;
  is_member: boolean;
  created_at: string;
}

interface UserRowProps {
  user: UserData;
  onEdit?: (user: UserData) => void;
  onDelete?: (user: UserData) => void;
  onToggleActive?: (user: UserData) => void;
  onChangeRole?: (user: UserData, newRole: "admin" | "member" | "user") => void;
  className?: string;
}

const roleColors = {
  admin: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  member: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  user: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300",
};

export function UserRow({ 
  user, 
  onEdit, 
  onDelete, 
  onToggleActive,
  onChangeRole,
  className 
}: UserRowProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div 
      className={cn(
        "bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700",
        "hover:border-blue-300 dark:hover:border-blue-600 transition-colors",
        className
      )}
    >
      <div className="flex items-center justify-between gap-4">
        {/* User Info */}
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0">
            {user.full_name ? (
              <span className="text-lg font-medium text-slate-600 dark:text-slate-300">
                {user.full_name.charAt(0).toUpperCase()}
              </span>
            ) : (
              <User className="w-5 h-5 text-slate-400" />
            )}
          </div>
          
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-900 dark:text-white truncate">
                {user.full_name || user.username}
              </h3>
              {user.is_member && (
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
              )}
              {!user.is_active && (
                <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
              )}
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1 truncate">
                <Mail className="w-3.5 h-3.5" />
                {user.email}
              </span>
              <span>•</span>
              <span>Joined {formatDate(user.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Role & Actions */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Role Badge */}
          <div className="relative">
            <button
              onClick={() => setShowRoleMenu(!showRoleMenu)}
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5",
                roleColors[user.role]
              )}
            >
              <Shield className="w-3.5 h-3.5" />
              {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
            </button>
            
            {showRoleMenu && (
              <div className="absolute right-0 top-full mt-1 w-40 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-10">
                {(["admin", "member", "user"] as const).map((role) => (
                  <button
                    key={role}
                    onClick={() => {
                      onChangeRole?.(user, role);
                      setShowRoleMenu(false);
                    }}
                    className={cn(
                      "w-full px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2",
                      user.role === role && "bg-slate-100 dark:bg-slate-700"
                    )}
                  >
                    <Shield className="w-3.5 h-3.5" />
                    {role.charAt(0).toUpperCase() + role.slice(1)}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Actions Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              <MoreVertical className="w-4 h-4 text-slate-500" />
            </button>
            
            {showMenu && (
              <div className="absolute right-0 top-full mt-1 w-44 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-10">
                <button
                  onClick={() => {
                    onEdit?.(user);
                    setShowMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2 text-slate-700 dark:text-slate-300"
                >
                  <Edit className="w-3.5 h-3.5" />
                  Edit User
                </button>
                <button
                  onClick={() => {
                    onToggleActive?.(user);
                    setShowMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2"
                >
                  {user.is_active ? (
                    <>
                      <Ban className="w-3.5 h-3.5" />
                      <span className="text-red-600">Deactivate</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span className="text-green-600">Activate</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    onDelete?.(user);
                    setShowMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2 text-red-600"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete User
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserRow;
