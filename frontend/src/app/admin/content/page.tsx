"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import {
  FolderOpen,
  FileText,
  Search,
  Trash2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface Project {
  id: number;
  name: string;
  description: string;
  owner_email: string;
  document_count: number;
  chat_session_count: number;
  created_at: string;
}

interface Document {
  id: number;
  filename: string;
  project_name: string;
  owner_email: string;
  file_type: string;
  file_size: number;
  created_at: string;
}

export default function AdminContent() {
  const [activeTab, setActiveTab] = useState<"projects" | "documents">("projects");
  const [projects, setProjects] = useState<Project[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (activeTab === "projects") {
      fetchProjects();
    } else {
      fetchDocuments();
    }
  }, [activeTab, page, search]);

  const fetchProjects = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(
        `http://localhost:8000/admin/projects?page=${page}&search=${search}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setProjects(data.items);
      }
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDocuments = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(
        `http://localhost:8000/admin/documents?page=${page}&search=${search}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.items);
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (id: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return;

    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`http://localhost:8000/admin/documents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchDocuments();
      }
    } catch (error) {
      console.error("Failed to delete document:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Content Management</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage projects and documents across all users
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab("projects")}
          className={`px-6 py-3 rounded-lg font-medium ${
            activeTab === "projects"
              ? "bg-primary-600 text-white"
              : "bg-white dark:bg-gray-800 hover:bg-gray-50"
          }`}
        >
          <FolderOpen className="w-5 h-5 inline mr-2" /
          Projects
        </button>
        <button
          onClick={() => setActiveTab("documents")}
          className={`px-6 py-3 rounded-lg font-medium ${
            activeTab === "documents"
              ? "bg-primary-600 text-white"
              : "bg-white dark:bg-gray-800 hover:bg-gray-50"
          }`}
        >
          <FileText className="w-5 h-5 inline mr-2" /
          Documents
        </button>
      </div>

      {/* Search */}
      <Card className="p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            placeholder={`Search ${activeTab}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      </Card>

      {/* Content */}
      {activeTab === "projects" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card key={project.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-xl">
                  <FolderOpen className="w-6 h-6 text-primary-600" />
                </div>
              </div>
              <h3 className="font-semibold mb-1">{project.name}</h3>
              <p className="text-sm text-gray-500 mb-4">{project.description}</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Owner</span>
                  <span>{project.owner_email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Documents</span>
                  <span>{project.document_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Chat Sessions</span>
                  <span>{project.chat_session_count}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left">Filename</th>
                <th className="px-6 py-3 text-left">Project</th>
                <th className="px-6 py-3 text-left">Owner</th>
                <th className="px-6 py-3 text-left">Type</th>
                <th className="px-6 py-3 text-left">Size</th>
                <th className="px-6 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td className="px-6 py-4">{doc.filename}</td>
                  <td className="px-6 py-4">{doc.project_name}</td>
                  <td className="px-6 py-4">{doc.owner_email}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-gray-100 rounded text-sm">
                      {doc.file_type}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {(doc.file_size / 1024).toFixed(1)} KB
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => deleteDocument(doc.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
