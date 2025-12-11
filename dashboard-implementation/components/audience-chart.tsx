interface AudienceData {
  label: string
  value: number
  color: string
}

interface AudienceChartProps {
  data?: AudienceData[]
  maxHeight?: number
}

const defaultAudienceData: AudienceData[] = [
  { label: "ЖЕНЩИНЫ\n25-35 ЛЕТ", value: 200, color: "#D1D5DB" },
  { label: "ОФИСНЫЕ\nРАБОТНИЦЫ", value: 180, color: "#1F2937" },
  { label: "АКТИВНЫЕ\nЖЕНЩИНЫ", value: 190, color: "#9CA3AF" },
  { label: "СТУДЕНТКИ\nИ МОЛОДЕЖЬ", value: 160, color: "#6B7280" },
  { label: "ПОКУПАТЕЛЬНИЦЫ\n36-45 ЛЕТ", value: 150, color: "#9CA3AF" },
]

export function AudienceChart({ data = defaultAudienceData, maxHeight = 200 }: AudienceChartProps) {
  const maxValue = Math.max(...data.map((item) => item.value))

  return (
    <div className="rounded-3xl bg-white p-6">
      <h3 className="mb-8 text-center text-[25px] font-bold uppercase leading-none">РАСПРЕДЕЛЕНИЕ ЦЕЛЕВОЙ АУДИТОРИИ</h3>

      <div className="flex items-end justify-center gap-8">
        {data.map((item, index) => (
          <div key={index} className="flex flex-col items-center gap-3">
            <div
              className="w-16 rounded-2xl transition-all duration-300"
              style={{
                height: `${(item.value / maxValue) * maxHeight}px`,
                backgroundColor: item.color,
              }}
            />
            <span className="whitespace-pre-line text-center text-xs font-medium text-muted-foreground">
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
