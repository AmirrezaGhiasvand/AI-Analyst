// components/dynamic-chart.tsx
"use client"

import {
  Bar,
  BarChart,
  Line,
  LineChart,
  Area,
  AreaChart,
  Pie,
  PieChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Cell,
} from "recharts"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart"

export type ChartType = "line" | "bar" | "area" | "pie"

export type ChartSpec = {
  chart_type: ChartType
  title: string
  x_label: string
  y_label: string
  x_key: string
  series_keys: string[]
  data: Record<string, number | string>[]
}

function buildConfig(seriesKeys: string[]): ChartConfig {
  return seriesKeys.reduce((config, key, i) => {
    config[key] = {
      label: key,
      color: `var(--chart-${(i % 5) + 1})`,
    }
    return config
  }, {} as ChartConfig)
}

function cleanData(
  data: Record<string, number | string | null>[],
  xKey: string,
  seriesKeys: string[]
) {
  const cleaned = data.filter((row) => {
    // drop rows missing the x value or where every series value is null
    if (row[xKey] === null || row[xKey] === undefined) return false
    return seriesKeys.some((key) => row[key] !== null && row[key] !== undefined)
  })

  const allNumericX = cleaned.every((row) => typeof row[xKey] === "number")
  if (allNumericX) {
    cleaned.sort((a, b) => (a[xKey] as number) - (b[xKey] as number))
  }

  return cleaned
}

export function DynamicChart({ spec }: { spec: ChartSpec }) {
  const { chart_type, title, x_key, series_keys, data } = spec
  const config = buildConfig(series_keys)
  const cleanedData = cleanData(data, x_key, series_keys)

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="h-[300px] w-full">
          {chart_type === "bar" ? (
            <BarChart accessibilityLayer data={cleanedData}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey={x_key}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis tickLine={false} axisLine={false} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              {series_keys.map((key) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={`var(--color-${key})`}
                  radius={4}
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          ) : chart_type === "line" ? (
            <LineChart accessibilityLayer data={cleanedData}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey={x_key}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis tickLine={false} axisLine={false} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              {series_keys.map((key) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={`var(--color-${key})`}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          ) : chart_type === "area" ? (
            <AreaChart accessibilityLayer data={cleanedData}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey={x_key}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis tickLine={false} axisLine={false} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              {series_keys.map((key) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  fill={`var(--color-${key})`}
                  stroke={`var(--color-${key})`}
                  fillOpacity={0.3}
                  isAnimationActive={false}
                />
              ))}
            </AreaChart>
          ) : chart_type === "pie" ? (
            <PieChart accessibilityLayer>
              <ChartTooltip content={<ChartTooltipContent />} />
              <Pie
                data={cleanedData}
                dataKey={series_keys[0]}
                nameKey={x_key}
                isAnimationActive={false}
              >
                {cleanedData.map((_, i) => (
                  <Cell key={i} fill={`var(--chart-${(i % 5) + 1})`} />
                ))}
              </Pie>
              <ChartLegend content={<ChartLegendContent />} />
            </PieChart>
          ) : (
            <div className="text-sm text-muted-foreground">
              Unsupported chart type: {chart_type}
            </div>
          )}
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
