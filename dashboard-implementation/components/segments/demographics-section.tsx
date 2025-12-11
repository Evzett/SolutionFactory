interface DemographicsData {
  malePercentage: number
  femalePercentage: number
  maleLabel?: string
  femaleLabel?: string
}

interface BarrierData {
  title: string
  items: string[]
}

interface DemographicsSectionProps {
  title?: string
  demographics: DemographicsData
  barriers: BarrierData[]
}

export function DemographicsSection({
  title = "ДЕМОГРАФИЯ ВАШЕЙ ЦЕЛЕВОЙ АУДИТОРИИ",
  demographics,
  barriers,
}: DemographicsSectionProps) {
  const circumference = 2 * Math.PI * 40 // r=40
  const femaleStroke = (demographics.femalePercentage / 100) * circumference

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Demographics Chart */}
      <div className="bg-white rounded-[30px] p-8">
        <h3 className="text-lg font-bold text-center mb-8 text-muted-foreground tracking-wide uppercase">{title}</h3>

        <div className="flex items-center justify-center gap-8">
          {/* Donut Chart - auto-scaled */}
          <div className="relative w-48 h-48">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              {/* Background circle (men) */}
              <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e5e5" strokeWidth="12" />
              {/* Foreground arc (women) - dynamic based on percentage */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="12"
                strokeDasharray={`${femaleStroke} ${circumference}`}
                strokeLinecap="round"
              />
            </svg>
          </div>

          {/* Legend - dynamic labels */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#e5e5e5]" />
              <span className="text-sm text-muted-foreground uppercase font-semibold">
                {demographics.maleLabel || "МУЖЧИНЫ"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#1a1a1a]" />
              <span className="text-sm text-muted-foreground uppercase font-semibold">
                {demographics.femaleLabel || "ЖЕНЩИНЫ"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Barriers - first 2 */}
      <div className="space-y-4">
        {barriers.slice(0, 2).map((barrier, index) => (
          <BarrierCard key={index} title={barrier.title} items={barrier.items} />
        ))}
      </div>

      {/* Barriers - remaining */}
      {barriers.length > 2 && (
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {barriers.slice(2).map((barrier, index) => (
            <BarrierCard key={index} title={barrier.title} items={barrier.items} />
          ))}
        </div>
      )}
    </div>
  )
}

interface BarrierCardProps {
  title: string
  items: string[]
}

function BarrierCard({ title, items }: BarrierCardProps) {
  return (
    <div className="bg-white rounded-[30px] p-6">
      <h4 className="font-semibold text-[15px] mb-4 text-muted-foreground tracking-wide uppercase">{title}</h4>

      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a] flex-shrink-0" />
            <span className="text-[15px] font-semibold uppercase leading-none">{item}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
