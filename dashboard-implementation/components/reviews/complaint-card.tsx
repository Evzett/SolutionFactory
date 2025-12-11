import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ComplaintCardProps {
  title: string
  subtitle: string
  issues: string[]
}

export function ComplaintCard({ title, subtitle, issues }: ComplaintCardProps) {
  return (
    <Card className="rounded-3xl border-0 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-[20px] font-semibold text-foreground uppercase">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-[15px] font-semibold text-muted-foreground mb-3 uppercase">{subtitle}</p>
        <ul className="space-y-2">
          {issues.map((issue, index) => (
            <li key={index} className="flex items-center gap-2 text-[15px] font-semibold text-foreground uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-foreground flex-shrink-0" />
              {issue}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
