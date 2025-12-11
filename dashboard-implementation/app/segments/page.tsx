import { AppNav } from "@/components/app-nav"
import { DistributionChart } from "@/components/segments/distribution-chart"
import { PortraitCards } from "@/components/segments/portrait-cards"
import { DemographicsSection } from "@/components/segments/demographics-section"
import { AgeChart } from "@/components/segments/age-chart"
import { MotivesCards } from "@/components/segments/motives-cards"
import { AuthGuard } from "@/components/auth-guard"

const distributionData = [
  { name: "ЖЕНЩИНЫ\n25-35 ЛЕТ", value: 200, color: "#c4c4c4" },
  { name: "ОФИСНЫЕ\nРАБОТНИЦЫ", value: 180, color: "#1a1a1a" },
  { name: "АКТИВНЫЕ\nЖЕНЩИНЫ", value: 190, color: "#d9d9d9" },
  { name: "СТУДЕНТКИ\nИ МОЛОДЕЖЬ", value: 160, color: "#a3a3a3" },
  { name: "ПОКУПАТЕЛЬНИЦЫ\n36-45 ЛЕТ", value: 150, color: "#737373" },
]

const portraitsData = [
  {
    title: "ОФИСНЫЕ РАБОТНИЦЫ",
    isDark: true,
    demographics: [
      { label: "ПОЛ", value: "ЖЕНСКИЙ" },
      { label: "ОБРАЗОВАНИЕ", value: "ВЫСШЕЕ" },
      { label: "УРОВЕНЬ ДОХОДА", value: "СРЕДНИЙ" },
      { label: "ВОЗРАСТ", value: "25-35 ЛЕТ" },
    ],
    description:
      "АКТИВНЫЕ ЖЕНЩИНЫ, РАБОТАЮЩИЕ В ОФИСЕ, ЦЕНЯТ КОМФОРТ И СТИЛЬ. ИЩУТ УНИВЕРСАЛЬНУЮ ОБУВЬ ДЛЯ РАБОТЫ И ПОВСЕДНЕВНОЙ НОСКИ",
    motives: "",
    barriers: "",
  },
  {
    title: "СТУДЕНТКИ И МОЛОДЕЖЬ",
    isDark: false,
    demographics: [
      { label: "ПОЛ", value: "ЖЕНСКИЙ" },
      { label: "ОБРАЗОВАНИЕ", value: "ВЫСШЕЕ (СТУДЕНТ)" },
      { label: "УРОВЕНЬ ДОХОДА", value: "НИЗКИЙ-СРЕДНИЙ" },
      { label: "ВОЗРАСТ", value: "18-25 ЛЕТ" },
    ],
    description:
      "МОЛОДЫЕ ДЕВУШКИ, АКТИВНО ЗАНИМАЮЩИЕСЯ СПОРТОМ И УЧЕБОЙ. ИЩУТ СТИЛЬНУЮ И КОМФОРТНУЮ ОБУВЬ ПО ДОСТУПНОЙ ЦЕНЕ",
  },
  {
    title: "АКТИВНЫЕ ЖЕНЩИНЫ",
    isDark: false,
    demographics: [
      { label: "ПОЛ", value: "ЖЕНСКИЙ" },
      { label: "ОБРАЗОВАНИЕ", value: "ВЫСШЕЕ" },
      { label: "УРОВЕНЬ ДОХОДА", value: "СРЕДНИЙ-ВЫСОКИЙ" },
      { label: "ВОЗРАСТ", value: "30-40 ЛЕТ" },
    ],
    description:
      "ЖЕНЩИНЫ, ВЕДУЩИЕ АКТИВНЫЙ ОБРАЗ ЖИЗНИ, ЗАНИМАЮЩИЕСЯ ФИТНЕСОМ И ЙОГОЙ. ЦЕНЯТ КАЧЕСТВО И ФУНКЦИОНАЛЬНОСТЬ ОБУВИ",
  },
  {
    title: "ПОКУПАТЕЛЬНИЦЫ 36-45 ЛЕТ",
    isDark: false,
    demographics: [
      { label: "ПОЛ", value: "ЖЕНСКИЙ" },
      { label: "ОБРАЗОВАНИЕ", value: "ВЫСШЕЕ" },
      { label: "УРОВЕНЬ ДОХОДА", value: "СРЕДНИЙ-ВЫСОКИЙ" },
      { label: "ВОЗРАСТ", value: "36-45 ЛЕТ" },
    ],
    description:
      "ЗРЕЛЫЕ ЖЕНЩИНЫ, ЦЕНЯЩИЕ КЛАССИЧЕСКИЙ СТИЛЬ И КАЧЕСТВО. ИЩУТ ЭЛЕГАНТНУЮ ОБУВЬ ДЛЯ РАБОТЫ И ОСОБЫХ СЛУЧАЕВ",
  },
]

const demographicsData = {
  malePercentage: 20,
  femalePercentage: 80,
  maleLabel: "МУЖЧИНЫ",
  femaleLabel: "ЖЕНЩИНЫ",
}

const barriersData = [
  {
    title: "ОСНОВНЫЕ БАРЬЕРЫ: (ОФИСНЫЕ РАБОТНИЦЫ)",
    items: ["НЕПОДХОДЯЩИЙ РАЗМЕР", "КАЧЕСТВО МАТЕРИАЛА", "ОГРАНИЧЕННЫЙ ВЫБОР ЦВЕТОВ", "ЦЕНА"],
  },
  {
    title: "ОСНОВНЫЕ БАРЬЕРЫ: (СТУДЕНТКИ)",
    items: ["ВЫСОКАЯ ЦЕНА", "НЕДОСТАТОК ИНФОРМАЦИИ", "СОМНЕНИЯ В КАЧЕСТВЕ", "ОГРАНИЧЕННЫЙ БЮДЖЕТ"],
  },
  {
    title: "ОСНОВНЫЕ БАРЬЕРЫ: (АКТИВНЫЕ ЖЕНЩИНЫ)",
    items: ["НЕДОСТАТОЧНАЯ АМОРТИЗАЦИЯ", "НЕПОДХОДЯЩИЙ ДИЗАЙН", "ОТСУТСТВИЕ НУЖНОГО РАЗМЕРА", "ДОЛГОВЕЧНОСТЬ"],
  },
  {
    title: "ОСНОВНЫЕ БАРЬЕРЫ: (36-45 ЛЕТ)",
    items: ["СТИЛЬ НЕ СООТВЕТСТВУЕТ ВОЗРАСТУ", "КОМФОРТ ПРИ ДОЛГОЙ НОСКЕ", "КАЧЕСТВО ИЗДЕЛИЯ", "СООТВЕТСТВИЕ ЦЕНЫ КАЧЕСТВУ"],
  },
]

const ageData = [
  { label: "18-25", value: 140, color: "#c4c4c4" },
  { label: "25-30", value: 200, color: "#1a1a1a" },
  { label: "30-35", value: 180, color: "#d9d9d9" },
  { label: "35-40", value: 160, color: "#a3a3a3" },
  { label: "40-45", value: 120, color: "#737373" },
]

const motivesData = [
  { title: "ОСНОВНЫЕ МОТИВЫ: (ОФИСНЫЕ РАБОТНИЦЫ)", items: ["УНИВЕРСАЛЬНОСТЬ", "КОМФОРТ НА РАБОТЕ", "КЛАССИЧЕСКИЙ СТИЛЬ", "СООТВЕТСТВИЕ ДРЕСС-КОДУ"] },
  { title: "ОСНОВНЫЕ МОТИВЫ: (СТУДЕНТКИ)", items: ["ДОСТУПНАЯ ЦЕНА", "СТИЛЬНЫЙ ВИД", "УДОБСТВО ДЛЯ ПОВСЕДНЕВНОЙ НОСКИ", "МОДНЫЙ ДИЗАЙН"] },
  { title: "ОСНОВНЫЕ МОТИВЫ: (АКТИВНЫЕ ЖЕНЩИНЫ)", items: ["ФУНКЦИОНАЛЬНОСТЬ", "КАЧЕСТВО МАТЕРИАЛОВ", "ПОДХОДИТ ДЛЯ ТРЕНИРОВОК", "ДЫШАЩИЕ МАТЕРИАЛЫ"] },
  { title: "ОСНОВНЫЕ МОТИВЫ: (36-45 ЛЕТ)", items: ["ЭЛЕГАНТНОСТЬ", "ДОЛГОВЕЧНОСТЬ", "КЛАССИЧЕСКИЙ ДИЗАЙН", "КАЧЕСТВО ИЗДЕЛИЯ"] },
]

export default function SegmentsPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#f0f0f0]">
        <AppNav className="pt-6 sm:pt-8 lg:pt-10" />

        <main className="px-4 sm:px-6 lg:px-8 py-8 flex justify-center">
          <div className="w-full max-w-[1292px] space-y-8">
            <DistributionChart segments={distributionData} />

            <section>
              <h2 className="text-[25px] font-bold text-center mb-8 tracking-wide uppercase">
                ПОРТРЕТ ЦЕЛЕВОЙ АУДИТОРИИ
              </h2>
              <PortraitCards portraits={portraitsData} />
            </section>

            <DemographicsSection demographics={demographicsData} barriers={barriersData} />

            <AgeChart ageGroups={ageData} />

            <MotivesCards motives={motivesData} />
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}

