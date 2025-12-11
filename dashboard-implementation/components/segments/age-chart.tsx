interface AgeGroupData {
  label: string
  value: number
  color: string
}

interface AgeChartProps {
  title?: string
  ageGroups: AgeGroupData[]
  maxHeight?: number
}

export function AgeChart({ title = "ВОЗРАСТ ВАШЕЙ ЦЕЛЕВОЙ АУДИТОРИИ", ageGroups, maxHeight = 200 }: AgeChartProps) {
  const maxValue = Math.max(...ageGroups.map((g) => g.value))

  return (
    <div className="bg-[#e8e8e8] rounded-[30px] p-8">
      <h2 className="text-[25px] font-bold text-center mb-12 tracking-wide uppercase">{title}</h2>

      <div className="flex items-end justify-between h-[250px] px-12">
        {ageGroups.map((group, index) => {
          const height = (group.value / maxValue) * maxHeight
          return (
            <div key={index} className="flex flex-col items-center gap-4 flex-1">
              <div
                className="w-[80px] rounded-[20px]"
                style={{
                  height,
                  backgroundColor: group.color,
                }}
              />
              <span className="text-xs text-muted-foreground text-center uppercase tracking-wider font-semibold">
                {group.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
