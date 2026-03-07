/**
 * ActivityChart - Line chart for activity over time
 * Displays user activity, chat counts, or other time-series data
 */

"use client";

import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ActivityDataPoint {
  date: string;
  value: number;
  label?: string;
}

interface ActivityChartProps {
  data: ActivityDataPoint[];
  title?: string;
  color?: string;
  showGrid?: boolean;
  showTooltip?: boolean;
  height?: number;
  className?: string;
}

export function ActivityChart({
  data,
  title,
  color = "#3B82F6",
  showGrid = true,
  showTooltip = true,
  height = 300,
  className
}: ActivityChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    value: number;
    label: string;
  } | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height });

  useEffect(() => {
    const updateDimensions = () => {
      if (canvasRef.current?.parentElement) {
        setDimensions({
          width: canvasRef.current.parentElement.clientWidth,
          height
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, [height]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length || dimensions.width === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = dimensions.width - padding.left - padding.right;
    const chartHeight = dimensions.height - padding.top - padding.bottom;

    // Clear canvas
    ctx.clearRect(0, 0, dimensions.width, dimensions.height);

    // Calculate scales
    const maxValue = Math.max(...data.map(d => d.value)) * 1.1;
    const minValue = 0;
    const valueRange = maxValue - minValue;

    const xStep = chartWidth / (data.length - 1 || 1);

    // Draw grid
    if (showGrid) {
      ctx.strokeStyle = "#E2E8F0";
      ctx.lineWidth = 1;

      // Horizontal grid lines
      const yLines = 5;
      for (let i = 0; i <= yLines; i++) {
        const y = padding.top + (chartHeight / yLines) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(dimensions.width - padding.right, y);
        ctx.stroke();

        // Y-axis labels
        const value = Math.round(maxValue - (valueRange / yLines) * i);
        ctx.fillStyle = "#64748B";
        ctx.font = "12px system-ui";
        ctx.textAlign = "right";
        ctx.fillText(value.toString(), padding.left - 8, y + 4);
      }

      // Vertical grid lines
      const xLines = Math.min(data.length, 7);
      for (let i = 0; i < xLines; i++) {
        const x = padding.left + (chartWidth / (xLines - 1 || 1)) * i;
        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, dimensions.height - padding.bottom);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // Draw line
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();

    data.forEach((point, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Fill area under line
    const gradient = ctx.createLinearGradient(0, padding.top, 0, dimensions.height - padding.bottom);
    gradient.addColorStop(0, `${color}33`);
    gradient.addColorStop(1, `${color}05`);
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(padding.left, dimensions.height - padding.bottom);
    data.forEach((point, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      ctx.lineTo(x, y);
    });
    ctx.lineTo(dimensions.width - padding.right, dimensions.height - padding.bottom);
    ctx.closePath();
    ctx.fill();

    // Draw points
    data.forEach((point, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#FFFFFF";
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    // X-axis labels
    ctx.fillStyle = "#64748B";
    ctx.font = "11px system-ui";
    ctx.textAlign = "center";
    const labelInterval = Math.ceil(data.length / 7);
    data.forEach((point, i) => {
      if (i % labelInterval === 0 || i === data.length - 1) {
        const x = padding.left + i * xStep;
        const label = point.label || point.date;
        ctx.fillText(label, x, dimensions.height - padding.bottom + 20);
      }
    });

  }, [data, dimensions, color, showGrid]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!showTooltip || !data.length || dimensions.width === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const padding = { left: 50, right: 20 };
    const chartWidth = dimensions.width - padding.left - padding.right;
    const xStep = chartWidth / (data.length - 1 || 1);

    const index = Math.round((x - padding.left) / xStep);
    if (index >= 0 && index < data.length) {
      const point = data[index];
      setTooltip({
        x: padding.left + index * xStep,
        y: y,
        value: point.value,
        label: point.label || point.date
      });
    }
  };

  return (
    <div className={cn("relative", className)}>
      {title && (
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          {title}
        </h3>
      )}
      
      <div style={{ height }}>
        <canvas
          ref={canvasRef}
          className="w-full"
          style={{ height: dimensions.height }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setTooltip(null)}
        />
      </div>

      {showTooltip && tooltip && (
        <div
          className="absolute pointer-events-none bg-slate-900 text-white text-sm rounded-lg px-3 py-2 shadow-lg z-10"
          style={{
            left: tooltip.x,
            top: tooltip.y - 60,
            transform: "translateX(-50%)"
          }}
        >
          <div className="font-semibold">{tooltip.value}</div>
          <div className="text-slate-300 text-xs">{tooltip.label}</div>
        </div>
      )}
    </div>
  );
}

export default ActivityChart;
