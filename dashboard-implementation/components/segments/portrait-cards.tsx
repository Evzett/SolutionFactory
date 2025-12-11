interface DemographicItem {
  label: string
  value: string
}

interface PortraitData {
  title: string
  isDark?: boolean
  demographics: DemographicItem[]
  description: string
  motives?: string
  barriers?: string
}

interface PortraitCardsProps {
  portraits: PortraitData[]
}

export function PortraitCards({ portraits }: PortraitCardsProps) {
  const firstRow = portraits.slice(0, 3)
  const secondRow = portraits.slice(3, 6)

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto">
      {/* First row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 justify-items-center">
        {firstRow.map((portrait, index) => (
          <PortraitCard key={index} {...portrait} />
        ))}
      </div>

      {/* Second row */}
      {secondRow.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 justify-items-center">
          {secondRow.map((portrait, index) => (
            <PortraitCard key={`row2-${index}`} {...portrait} />
          ))}
        </div>
      )}
    </div>
  )
}

function PortraitCard({ title, isDark, demographics, description, motives, barriers }: PortraitData) {
  return (
    <div
      className={`rounded-[50px] p-8 w-full max-w-[367px] min-h-[422px] flex flex-col ${
        isDark ? "bg-[#1a1a1a] text-white" : "bg-white text-foreground"
      }`}
    >
      <h3 className="font-bold text-lg mb-6 uppercase">{title}</h3>

      <div className="space-y-3 mb-6">
        {demographics.map((item, index) => (
          <div key={index} className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isDark ? "bg-gray-500" : "bg-gray-400"}`} />
            <span className="text-[15px] font-semibold uppercase leading-none">
              {item.label}: {item.value}
            </span>
          </div>
        ))}
      </div>

      <p
        className={`text-[15px] font-semibold uppercase leading-relaxed ${isDark ? "text-gray-300" : "text-muted-foreground"}`}
      >
        {description}
        {motives && (
          <>
            <br />
            <br />
            <span className="font-bold">МОТИВЫ (ПОЧЕМУ ПОКУПАЮТ):</span>
            <br />
            <span>{motives}</span>
          </>
        )}
        {barriers && (
          <>
            <br />
            <span className="font-bold">БАРЬЕРЫ (ПОЧЕМУ НЕ ПОКУПАЮТ):</span>
            <br />
            <span>{barriers}</span>
          </>
        )}
      </p>
    </div>
  )
}
