import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Product {
  name: string
  values: number[]
}

interface TopProductsCardProps {
  title: string
  products: Product[]
}

export function TopProductsCard({ title, products }: TopProductsCardProps) {
  return (
    <Card className="rounded-3xl border-0 shadow-none">
      <CardHeader className="pb-4">
        <CardTitle className="text-[20px] font-semibold text-foreground uppercase">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {products.map((product, index) => (
          <div key={index} className="flex items-center gap-4">
            <div className="flex-1 flex h-8 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#3a3a3a] transition-all duration-500"
                style={{ width: `${product.values[0]}%` }}
              />
              <div
                className="h-full bg-[#8a8a8a] transition-all duration-500"
                style={{ width: `${product.values[1]}%` }}
              />
            </div>
            <span className="text-[15px] font-semibold text-muted-foreground whitespace-nowrap min-w-[200px] uppercase">
              {product.name}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
