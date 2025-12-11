import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Topic {
  name: string
  value: number
  color: string
}

interface HotTopicsCardProps {
  title: string
  topics: Topic[]
}

export function HotTopicsCard({ title, topics }: HotTopicsCardProps) {
  const maxValue = Math.max(...topics.map((t) => t.value))

  return (
    <Card className="rounded-3xl border-0 shadow-none">
      <CardHeader className="pb-4">
        <CardTitle className="text-[20px] font-semibold text-center text-foreground uppercase">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-center gap-16 h-[400px] pb-8">
          {topics.map((topic, index) => (
            <div key={index} className="flex flex-col items-center gap-4">
              <div
                className="w-20 rounded-2xl transition-all duration-500"
                style={{
                  height: `${(topic.value / maxValue) * 280}px`,
                  backgroundColor: topic.color,
                }}
              />
              <span className="text-[15px] font-semibold text-muted-foreground uppercase">{topic.name}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
