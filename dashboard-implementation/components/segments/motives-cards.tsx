interface MotiveData {
  title: string
  items: string[]
}

interface MotivesCardsProps {
  motives: MotiveData[]
}

export function MotivesCards({ motives }: MotivesCardsProps) {
  return (
    <div className="bg-[#e8e8e8] rounded-[30px] p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {motives.map((motive, index) => (
          <div key={index} className="bg-white rounded-[30px] p-6">
            <h4 className="font-semibold text-[15px] mb-4 tracking-wide uppercase">{motive.title}</h4>

            <div className="space-y-3">
              {motive.items.map((item, itemIndex) => (
                <div key={itemIndex} className="flex items-center gap-3">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a] flex-shrink-0" />
                  <span className="text-[15px] font-semibold uppercase leading-none">{item}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
