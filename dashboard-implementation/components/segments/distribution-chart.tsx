interface SegmentData {
  name: string
  value: number
  color: string
}

interface DistributionChartProps {
  title?: string
  segments: SegmentData[]
  maxHeight?: number
}

export function DistributionChart({
  title = "РАСПРЕДЕЛЕНИЕ ЦЕЛЕВОЙ АУДИТОРИИ",
  segments,
  maxHeight = 240,
}: DistributionChartProps) {
  const maxValue = Math.max(...segments.map((s) => s.value))

  return (
    <div className="bg-white rounded-[30px] p-8">
      <h2 className="text-[25px] font-bold text-center mb-12 tracking-wide uppercase">{title}</h2>

      <div className="flex items-end justify-between h-[300px] px-8">
        {segments.map((segment, index) => {
          const height = (segment.value / maxValue) * maxHeight
          return (
            <div key={index} className="flex flex-col items-center gap-4 flex-1">
              <div
                className="w-[70px] rounded-[20px]"
                style={{
                  height,
                  backgroundColor: segment.color,
                }}
              />
              <span className="text-xs text-muted-foreground text-center whitespace-pre-line uppercase tracking-wider font-semibold">
                {segment.name}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
