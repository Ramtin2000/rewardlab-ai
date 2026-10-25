"use client";

import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

export interface MetricSeries {
  id: string;
  name: string;
  color: string;
  points: { step: number; value: number }[];
}

// One metric (0..1) over training steps, one line per run.
// The untrained baseline is a dashed reference line, not a series.
export function MetricChart({
  series,
  baseline,
  className,
}: {
  series: MetricSeries[];
  baseline?: { name: string; value: number; color: string };
  className?: string;
}) {
  const config: ChartConfig = Object.fromEntries(series.map((s) => [s.id, { label: s.name, color: s.color }]));

  const steps = [...new Set(series.flatMap((s) => s.points.map((p) => p.step)))].sort((a, b) => a - b);
  const data = steps.map((step) => ({
    step,
    ...Object.fromEntries(series.map((s) => [s.id, s.points.find((p) => p.step === step)?.value])),
  }));

  return (
    <ChartContainer config={config} className={className ?? "aspect-auto h-56 w-full"}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid vertical={false} stroke="var(--grid)" />
        <XAxis dataKey="step" tickLine={false} axisLine={false} tickMargin={8} fontSize={11} />
        <YAxis
          domain={[0, 1]}
          ticks={[0, 0.25, 0.5, 0.75, 1]}
          tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
          tickLine={false}
          axisLine={false}
          fontSize={11}
        />
        {baseline && (
          <ReferenceLine
            y={baseline.value}
            stroke={baseline.color}
            strokeDasharray="4 4"
            label={{ value: baseline.name, position: "insideBottomRight", fontSize: 10, fill: "var(--muted-foreground)" }}
          />
        )}
        <ChartTooltip
          cursor={{ stroke: "var(--border)" }}
          content={
            <ChartTooltipContent
              labelFormatter={(_, payload) => `Step ${payload?.[0]?.payload?.step}`}
              formatter={(value, name) => (
                <div className="flex w-full items-center justify-between gap-4">
                  <span className="text-muted-foreground">{config[name as string]?.label}</span>
                  <span className="font-mono font-medium tabular-nums text-foreground">
                    {Math.round(Number(value) * 100)}%
                  </span>
                </div>
              )}
            />
          }
        />
        <ChartLegend content={<ChartLegendContent />} />
        {series.map((s) => (
          <Line
            key={s.id}
            dataKey={s.id}
            type="monotone"
            stroke={`var(--color-${s.id})`}
            strokeWidth={2}
            dot={{ r: 4, strokeWidth: 2, stroke: "var(--card)", fill: `var(--color-${s.id})` }}
            activeDot={{ r: 5, strokeWidth: 2, stroke: "var(--card)", fill: `var(--color-${s.id})` }}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ChartContainer>
  );
}
