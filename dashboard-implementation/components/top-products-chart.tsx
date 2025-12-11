interface Product {
  name: string
  value: number
}

interface TopProductsChartProps {
  data?: Product[]
}

const defaultProducts: Product[] = [
  { name: "ЛОФЕРЫ LOOKING.SHIK ЧЕРНЫЙ ЛАК", value: 95 },
  { name: "КРОССОВКИ LOOKING.SHIK", value: 88 },
  { name: "ЛОФЕРЫ LOOKING.SHIK БОРДО", value: 82 },
]

export function TopProductsChart({ data = defaultProducts }: TopProductsChartProps) {
  const maxValue = Math.max(...data.map((p) => p.value))

  return (
    <div className="rounded-3xl bg-white p-6">
      <h3 className="mb-6 text-[25px] font-bold uppercase leading-none">ТОП-5 ПРОДУКТОВ:</h3>

      <div className="space-y-4">
        {data.map((product, index) => (
          <div key={index} className="flex items-center gap-4">
            <div className="h-4 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${(product.value / maxValue) * 100}%`,
                  backgroundColor: index % 2 === 0 ? "#8B9A5C" : "#6B7280",
                }}
              />
            </div>
            <span className="w-44 shrink-0 text-xs font-medium text-muted-foreground">{product.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
