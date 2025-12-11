interface TipsCardProps {
  tips?: string[]
  additionalText?: string
}

const defaultTips = [
  "ДОБАВЬТЕ БОЛЬШЕ ФОТОГРАФИЙ ТОВАРОВ С РАЗНЫХ РАКУРСОВ",
  "УЛУЧШИТЕ ОПИСАНИЯ ТОВАРОВ: ДОБАВЬТЕ ДЕТАЛИ О МАТЕРИАЛАХ И РАЗМЕРАХ",
  "ДОБАВЬТЕ ВИДЕО ОБЗОРЫ ТОВАРОВ ДЛЯ ЛУЧШЕГО ВОСПРИЯТИЯ",
]
const defaultAdditionalText = "РЕКОМЕНДУЕМ РАСШИРИТЬ АССОРТИМЕНТ ЦВЕТОВ И РАЗМЕРОВ ДЛЯ УВЕЛИЧЕНИЯ КОНВЕРСИИ"

export function TipsCard({ tips = defaultTips, additionalText = defaultAdditionalText }: TipsCardProps) {
  return (
    <div className="rounded-3xl bg-foreground p-6 text-background">
      <h3 className="mb-4 text-center text-[20px] font-bold uppercase leading-none">СОВЕТЫ ПО УЛУЧШЕНИЯМ</h3>

      <ul className="space-y-2">
        {tips.map((tip, index) => (
          <li key={index} className="flex items-start gap-2">
            <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#8B9A5C]" />
            <span className="text-xs font-medium">{tip}</span>
          </li>
        ))}
      </ul>

      {additionalText && <p className="mt-4 text-xs font-medium leading-tight">{additionalText}</p>}
    </div>
  )
}
