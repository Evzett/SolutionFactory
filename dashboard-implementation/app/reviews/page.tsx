import { AppNav } from "@/components/app-nav"
import { TopProductsCard } from "@/components/reviews/top-products-card"
import { HotTopicsCard } from "@/components/reviews/hot-topics-card"
import { ComplaintCard } from "@/components/reviews/complaint-card"
import { AuthGuard } from "@/components/auth-guard"

const topProducts = [
  { name: "ЛОФЕРЫ LOOKING.SHIK ЧЕРНЫЙ ЛАК", values: [85, 15] },
  { name: "КРОССОВКИ LOOKING.SHIK", values: [78, 22] },
  { name: "ЛОФЕРЫ LOOKING.SHIK БОРДО", values: [72, 28] },
]

const hotTopics = [
  { name: "КАЧЕСТВО", value: 85, color: "#e0e0e0" },
  { name: "ДОСТАВКА", value: 65, color: "#1a1a1a" },
  { name: "РАЗМЕР", value: 70, color: "#c0c0c0" },
  { name: "ЦВЕТ", value: 90, color: "#d0d0d0" },
  { name: "УПАКОВКА", value: 75, color: "#808080" },
]

const complaints = [
  {
    title: "ЛОФЕРЫ LOOKING.SHIK ЧЕРНЫЙ ЛАК",
    subtitle: "ЛЮДИ ЧАЩЕ ВСЕГО ПИШУТ:",
    issues: ["НЕПОДХОДЯЩИЙ РАЗМЕР", "ТРЕЩИНЫ НА ПОДОШВЕ", "ТУГАЯ ПОСАДКА", "БЫСТРО СТИРАЕТСЯ"],
  },
  {
    title: "КРОССОВКИ LOOKING.SHIK",
    subtitle: "ЛЮДИ ЧАЩЕ ВСЕГО ПИШУТ:",
    issues: ["НЕДОСТАТОЧНАЯ АМОРТИЗАЦИЯ", "МАЛОМЕРИТ", "СКОЛЬЗКАЯ ПОДОШВА", "ТЕСНО В НОСКЕ"],
  },
]

const complaintsTitle = "НА ЭТИ ТОВАРЫ ЖАЛУЮТСЯ ЧАЩЕ ВСЕГО:"

export default function ReviewsPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#f5f5f5]">
        <AppNav className="pt-6 sm:pt-8 lg:pt-10" />

        <main className="w-full px-4 sm:px-6 lg:px-8 py-8 flex flex-col items-center gap-8">
          <div className="w-full max-w-[1292px] space-y-8">
            <TopProductsCard title="ТОП-3 ПРОДУКТОВ:" products={topProducts} />

            <section>
              <h2 className="text-[20px] font-semibold text-center mb-6 text-foreground uppercase">{complaintsTitle}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {complaints.map((complaint, index) => (
                  <ComplaintCard
                    key={index}
                    title={complaint.title}
                    subtitle={complaint.subtitle}
                    issues={complaint.issues}
                  />
                ))}
              </div>
            </section>

            <HotTopicsCard title="ГОРЯЧИЕ ТЕМЫ ОТЗЫВОВ" topics={hotTopics} />
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}

