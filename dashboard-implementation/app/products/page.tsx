import { ProductsPage } from "@/components/products-page"
import { AuthGuard } from "@/components/auth-guard"

export default function ProductsRoute() {
  return (
    <AuthGuard>
      <ProductsPage />
    </AuthGuard>
  )
}

