interface TopProductsCardProps {
  value: string
  label: string
}

export function TopProductsCard({ value, label }: TopProductsCardProps) {
  return (
    <div className="flex flex-col items-center rounded-3xl bg-white p-6 text-center">
      <div className="text-5xl font-bold">{value}</div>
      <div className="mt-1 max-w-[200px] text-sm font-bold uppercase text-muted-foreground">{label}</div>
    </div>
  )
}
