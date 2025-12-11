import { AppNav } from "@/components/app-nav"
import { TipsCard } from "@/components/tips-card"
import { RatingCard } from "@/components/rating-card"
import { TopProductsCard } from "@/components/top-products-card"
import { TopProductsChart } from "@/components/top-products-chart"
import { ReviewsChart } from "@/components/reviews-chart"
import { AudienceChart } from "@/components/audience-chart"
import { AuthGuard } from "@/components/auth-guard"

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#f5f5f5] pt-6 sm:pt-8 lg:pt-10 px-4 sm:px-6 lg:px-8 pb-6">
        <AppNav className="pb-4" />

        {/* Top row cards */}
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3 max-w-[1292px] mx-auto">
          <TipsCard />
          <RatingCard value="4,9+" label="ВАШ СРЕДНИЙ РЕЙТИНГ" />
          <TopProductsCard value="3" label="ТОВАРОВ, ВХОДЯЩИХ В ТОП УНИКАЛЬНЫХ ПРОДАЖ" />
        </div>

        {/* Middle row - Top products and reviews */}
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 max-w-[1292px] mx-auto">
          <TopProductsChart />
          <ReviewsChart />
        </div>

        {/* Bottom row - Audience distribution */}
        <div className="mt-4 max-w-[1292px] mx-auto">
          <AudienceChart />
        </div>
      </div>
    </AuthGuard>
  )
}
