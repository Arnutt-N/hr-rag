"use client";

import { useState, useEffect, useCallback } from "react";

interface Project {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at: string;
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const token = localStorage.getItem("token");

    try {
      const res = await fetch("http://localhost:8000/api/projects", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Failed to fetch projects");

      const data = await res.json();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createProject = async (name: string, description?: string) => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("http://localhost:8000/api/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, description }),
      });

      if (!res.ok) throw new Error("Failed to create project");

      await fetchProjects();
      return true;
    } catch (error) {
      return false;
    }
  };

  const deleteProject = async (id: string) => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Failed to delete project");

      await fetchProjects();
      return true;
    } catch (error) {
      return false;
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return {
    projects,
    isLoading,
    error,
    fetchProjects,
    createProject,
    deleteProject,
  };
}
