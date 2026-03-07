/**
 * ProviderUsageChart - Pie chart for LLM provider usage
 * Displays distribution of LLM provider usage
 */

"use client";

import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ProviderData {
  name: string;
  value: number;
  color?: string;
}

interface ProviderUsageChartProps {
  data: ProviderData[];
  title?: string;
  showLegend?: boolean;
  showLabels?: boolean;
  size?: number;
  className?: string;
}

const defaultColors = [
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#EF4444", // Red
  "#8B5CF6", // Violet
  "#EC4899", // Pink
  "#06B6D4", // Cyan
  "#84CC16", // Lime
];

export function ProviderUsageChart({
  data,
  title,
  showLegend = true,
  showLabels = true,
  size = 240,
  className
}: ProviderUsageChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeSegment, setActiveSegment] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    name: string;
    value: number;
    percentage: number;
  } | null>(null);

  const total = data.reduce((sum, d) => sum + d.value, 0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 10;
    const innerRadius = radius * 0.6;

    let startAngle = -Math.PI / 2;

    data.forEach((segment, index) => {
      const sliceAngle = (segment.value / total) * Math.PI * 2;
      const endAngle = startAngle + sliceAngle;
      const isActive = activeSegment === index;

      // Draw segment
      ctx.beginPath();
      ctx.moveTo(
        centerX + Math.cos(startAngle) * innerRadius,
        centerY + Math.sin(startAngle) * innerRadius
      );
      ctx.arc(centerX, centerY, isActive ? radius + 5 : radius, startAngle, endAngle);
      ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
      ctx.closePath();

      ctx.fillStyle = segment.color || defaultColors[index % defaultColors.length];
      ctx.fill();

      // Draw label
      if (showLabels && total > 0) {
        const midAngle = startAngle + sliceAngle / 2;
        const labelRadius = radius * 0.8;
        const labelX = centerX + Math.cos(midAngle) * labelRadius;
        const labelY = centerY + Math.sin(midAngle) * labelRadius;

        const percentage = ((segment.value / total) * 100).toFixed(1);
        if (parseFloat(percentage) >= 5) {
          ctx.fillStyle = "#FFFFFF";
          ctx.font = "bold 12px system-ui";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(`${percentage}%`, labelX, labelY);
        }
      }

      startAngle = endAngle;
    });

  }, [data, size, total, activeSegment, showLabels]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    const distance = Math.sqrt(x * x + y * y);
    const radius = size / 2 - 10;
    const innerRadius = radius * 0.6;

    if (distance < innerRadius || distance > radius + 5) {
      setActiveSegment(null);
      setTooltip(null);
      return;
    }

    let angle = Math.atan2(y, x) + Math.PI / 2;
    if (angle < 0) angle += Math.PI * 2;

    let accumulatedAngle = 0;
    for (let i = 0; i < data.length; i++) {
      const sliceAngle = (data[i].value / total) * Math.PI * 2;
      if (angle >= accumulatedAngle && angle < accumulatedAngle + sliceAngle) {
        setActiveSegment(i);
        const percentage = (data[i].value / total) * 100;
        setTooltip({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
          name: data[i].name,
          value: data[i].value,
          percentage
        });
        return;
      }
      accumulatedAngle += sliceAngle;
    }
  };

  return (
    <div className={cn("flex flex-col", className)}>
      {title && (
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          {title}
        </h3>
      )}

      <div className="flex items-center gap-8 flex-wrap">
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={size}
            height={size}
            className="cursor-pointer"
            onMouseMove={handleMouseMove}
            onMouseLeave={() => {
              setActiveSegment(null);
              setTooltip(null);
            }}
          />

          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {total.toLocaleString()}
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Total
            </span>
          </div>

          {/* Tooltip */}
          {tooltip && (
            <div
              className="absolute pointer-events-none bg-slate-900 text-white text-sm rounded-lg px-3 py-2 shadow-lg z-10"
              style={{
                left: tooltip.x,
                top: tooltip.y - 60,
                transform: "translateX(-50%)"
              }}
            >
              <div className="font-semibold">{tooltip.name}</div>
              <div className="text-slate-300 text-xs">
                {tooltip.value.toLocaleString()} ({tooltip.percentage.toFixed(1)}%)
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        {showLegend && (
          <div className="flex flex-col gap-2">
            {data.map((item, index) => (
              <div
                key={item.name}
                className={cn(
                  "flex items-center gap-2 px-2 py-1 rounded transition-colors cursor-pointer",
                  activeSegment === index && "bg-slate-100 dark:bg-slate-700"
                )}
                onMouseEnter={() => setActiveSegment(index)}
                onMouseLeave={() => setActiveSegment(null)}
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color || defaultColors[index % defaultColors.length] }}
                />
                <span className="text-sm text-slate-600 dark:text-slate-300">
                  {item.name}
                </span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">
                  {item.value.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProviderUsageChart;
