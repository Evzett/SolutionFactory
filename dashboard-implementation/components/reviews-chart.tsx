"use client"

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

interface ReviewData {
  name: string
  value: number
  color: string
}

interface ReviewsChartProps {
  data?: ReviewData[]
}

const defaultData: ReviewData[] = [
  { name: "ОТЛИЧНОЕ КАЧЕСТВО, УДОБНЫЕ", value: 65, color: "#E5E7EB" },
  { name: "КРАСИВЫЕ, НО МАЛОМЕРЯТ", value: 20, color: "#1F2937" },
  { name: "СТИЛЬНЫЕ, ПОДХОДЯТ К ОФИСНОМУ СТИЛЮ", value: 15, color: "#9CA3AF" },
]

export function ReviewsChart({ data = defaultData }: ReviewsChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="rounded-3xl bg-white p-6">
      <h3 className="mb-4 text-center text-[25px] font-bold uppercase leading-none">ВАШИ ОТЗЫВЫ:</h3>

      <div className="flex items-center justify-center gap-8">
        <div className="h-40 w-40">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={70}
                paddingAngle={0}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-4">
          {data.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <span className="h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-xs font-medium text-muted-foreground">{item.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
