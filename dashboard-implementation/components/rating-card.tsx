interface RatingCardProps {
  value: string
  label: string
}

export function RatingCard({ value, label }: RatingCardProps) {
  return (
    <div className="rounded-3xl bg-white p-6">
      <div className="text-5xl font-bold">{value}</div>
      <div className="mt-1 text-sm font-bold uppercase text-muted-foreground">{label}</div>
    </div>
  )
}
