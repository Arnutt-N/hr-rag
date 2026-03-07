"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  Play,
  History,
  Target,
  AlertTriangle,
  CheckCircle,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";

interface EvaluationMetrics {
  precision_at_k: number;
  recall_at_k: number;
  mrr: number;
  ndcg: number;
  hit_rate: number;
  faithfulness: number;
  answer_relevance: number;
  context_precision: number;
  context_recall: number;
  hallucination_rate: number;
  accuracy: number;
  response_time: number;
  thai_tokenization_score: number;
  thai_semantic_similarity: number;
}

interface EvaluationResult {
  evaluation_id: string;
  metrics: EvaluationMetrics;
  overall_score: number;
  test_cases_evaluated: number;
  evaluation_time: number;
  timestamp: string;
  provider: string;
}

interface DashboardData {
  total_evaluations: number;
  average_score: number;
  latest_metrics: EvaluationMetrics;
  latest_evaluation_id: string;
  latest_timestamp: string;
  trends: Record<string, { change: number; trend: string }>;
}

export default function EvaluationPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("openai");
  const [lastResult, setLastResult] = useState<EvaluationResult | null>(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("http://localhost:8000/api/evaluation/dashboard", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const runEvaluation = async () => {
    setIsRunning(true);
    const token = localStorage.getItem("token");

    try {
      const res = await fetch("http://localhost:8000/api/evaluation/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider: selectedProvider,
          test_dataset: "hr_default",
          k: 5,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setLastResult(data);
        fetchDashboard();
      }
    } catch (error) {
      console.error("Failed to run evaluation:", error);
    } finally {
      setIsRunning(false);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "improving":
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case "declining":
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Link
              href="/chat"
              className="mr-4 p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg"
            >
              <ChevronLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold">ประเมินผล RAG System</h1>
              <p className="text-gray-600 dark:text-gray-400">
                วัดประสิทธิภาพระบบตามมาตรฐาน RAGAS
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="groq">Groq</option>
            </select>
            <Button onClick={runEvaluation} disabled={isRunning}>
              {isRunning ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  กำลังประเมิน...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  รันการประเมิน
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Overall Score Card */}
        {dashboard && dashboard.total_evaluations > 0 && (
          <Card className="p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-1">Overall Score</p>
                <p
                  className={`text-4xl font-bold ${getScoreColor(
                    dashboard.average_score
                  )}`}
                >
                  {(dashboard.average_score * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-1">Total Evaluations</p>
                <p className="text-4xl font-bold">
                  {dashboard.total_evaluations}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-1">Latest Provider</p>
                <p className="text-2xl font-bold capitalize">
                  {lastResult?.provider || "-"}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-1">Last Run</p>
                <p className="text-sm">
                  {lastResult
                    ? new Date(lastResult.timestamp).toLocaleString("th-TH")
                    : "-"}
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Latest Results */}
        {(lastResult || dashboard?.latest_metrics) && (
          <>
            <h2 className="text-xl font-semibold mb-4">ผลการประเมินล่าสุด</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {lastResult &&
                Object.entries(lastResult.metrics).map(([key, value]) => (
                  <Card key={key} className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 capitalize">
                          {key.replace(/_/g, " ")}
                        </p>
                        <p className={`text-2xl font-bold ${getScoreColor(value)}`}>
                          {(value * 100).toFixed(1)}%
                        </p>
                      </div>
                      {dashboard?.trends?.[key] && (
                        <div className="flex items-center">
                          {getTrendIcon(dashboard.trends[key].trend)}
                          <span
                            className={`ml-1 text-sm ${
                              dashboard.trends[key].change > 0
                                ? "text-green-600"
                                : dashboard.trends[key].change < 0
                                ? "text-red-600"
                                : "text-gray-500"
                            }`}
                          >
                            {dashboard.trends[key].change > 0 ? "+" : ""}
                            {(dashboard.trends[key].change * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
            </div>
          </>
        )}

        {/* Target Metrics */}
        <h2 className="text-xl font-semibold mb-4">ค่าเป้าหมาย (HR Policy)</h2>
        <Card className="p-6 mb-8">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { name: "Precision@K", target: 0.85, min: 0.75 },
              { name: "Recall@K", target: 0.80, min: 0.70 },
              { name: "Faithfulness", target: 0.90, min: 0.80 },
              { name: "Answer Relevance", target: 0.85, min: 0.75 },
              { name: "Hallucination Rate", target: 0.05, max: 0.15 },
              { name: "Response Time", target: 2.0, max: 5.0, unit: "s" },
            ].map((metric) => (
              <div key={metric.name} className="flex items-center gap-3">
                <Target className="w-5 h-5 text-primary-600" />
                <div>
                  <p className="text-sm font-medium">{metric.name}</p>
                  <p className="text-xs text-gray-500">
                    Target: {metric.target}
                    {metric.unit || ""} | Min: {metric.min || metric.max}
                    {metric.unit || ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6">
            <div className="flex items-start gap-3">
              <BarChart3 className="w-6 h-6 text-primary-600 mt-1" />
              <div>
                <h3 className="font-semibold mb-2">Metrics ที่ประเมิน</h3>
                <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Precision@K, Recall@K, MRR, NDCG, Hit Rate</li>
                  <li>• Faithfulness, Answer Relevance</li>
                  <li>• Context Precision, Context Recall</li>
                  <li>• Hallucination Rate, Accuracy</li>
                  <li>• Thai Tokenization & Semantic Similarity</li>
                </ul>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start gap-3">
              <History className="w-6 h-6 text-primary-600 mt-1" />
              <div>
                <h3 className="font-semibold mb-2">Test Dataset</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  ชุดทดสอบประกอบด้วย:
                </p>
                <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Easy queries - คำถามง่าย</li>
                  <li>• Complex queries - คำถามซับซ้อน</li>
                  <li>• Edge cases - กรณีพิเศษ</li>
                  <li>• Out of scope - นอกขอบเขต</li>
                  <li>• Multi-hop - หลายขั้นตอน</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
