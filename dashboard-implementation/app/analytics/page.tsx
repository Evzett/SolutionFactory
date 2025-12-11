"use client"

import { useState } from "react"
import { ArrowUpCircle } from "lucide-react"
import { AppNav } from "@/components/app-nav"
import { AuthGuard } from "@/components/auth-guard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { setImportAccess } from "@/lib/import-access"

export default function AnalyticsPage() {
  const [link, setLink] = useState("")
  const [submitted, setSubmitted] = useState(() => {
    if (typeof window === "undefined") return false
    return window.localStorage.getItem("import_access_granted") === "true"
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!link.trim()) return
    setImportAccess(true)
    setSubmitted(true)
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#f5f5f5] relative overflow-hidden">
        <div className="absolute right-0 top-0 w-[40%] max-w-[600px] h-[50%] max-h-[500px] pointer-events-none hidden md:block z-0">
          <svg viewBox="0 0 600 500" className="w-full h-full" preserveAspectRatio="none">
            <path d="M 600 500 Q 400 250, 415 0" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 600 460 Q 420 230, 445 0" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 600 420 Q 450 210, 475 0" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 600 380 Q 480 190, 505 0" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 600 340 Q 510 170, 535 0" fill="none" stroke="#1a1a1a" strokeWidth="3" />
          </svg>
        </div>

        <div className="absolute bottom-0 left-0 w-[35%] max-w-[500px] h-[40%] max-h-[300px] pointer-events-none hidden md:block z-0">
          <svg viewBox="0 0 500 300" className="w-full h-full" preserveAspectRatio="none">
            <path d="M 0 60 Q 280 40, 440 300" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 0 100 Q 180 20, 380 300" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 0 140 Q 200 40, 320 300" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 0 180 Q 160 60, 280 300" fill="none" stroke="#1a1a1a" strokeWidth="3" />
            <path d="M 0 220 Q 150 80, 240 300" fill="none" stroke="#1a1a1a" strokeWidth="3" />
          </svg>
        </div>

        <AppNav className="pt-6 sm:pt-8 lg:pt-10 relative z-10" />

        <div className="flex justify-center">
          <main className="px-4 sm:px-6 lg:px-8 pt-8 sm:pt-12 lg:pt-16 pb-16 sm:pb-24 lg:pb-32 relative z-10 w-full max-w-[1292px]">
            <h1
              className="font-bold text-black uppercase mb-4 sm:mb-6 text-3xl sm:text-4xl md:text-5xl lg:text-[60px]"
              style={{
                fontFamily: "var(--font-golos), sans-serif",
                lineHeight: "100%",
                letterSpacing: "0%",
              }}
            >
              АНАЛИТИКА,
              <br />
              КОТОРАЯ ВИДИТ БОЛЬШЕ
            </h1>

            <p
              className="font-semibold lowercase mb-8 sm:mb-12 lg:mb-16 text-lg sm:text-xl md:text-2xl lg:text-[30px]"
              style={{
                fontFamily: "var(--font-golos), sans-serif",
                lineHeight: "100%",
                letterSpacing: "0%",
                color: "#777575",
              }}
            >
              загрузите данные
              <br />и откройте настоящую картину вашей аудитории
            </p>

            <form
              onSubmit={handleSubmit}
              className="relative w-full max-w-[961px] h-[50px] sm:h-[58px] lg:h-[65px] flex gap-3"
            >
              <Input
                value={link}
                onChange={(e) => setLink(e.target.value)}
                placeholder="Вставьте ссылку для импорта"
                className="h-full bg-white border border-border text-foreground placeholder:text-muted-foreground rounded-full text-sm sm:text-base px-5"
              />
              <Button
                type="submit"
                className="h-full rounded-full px-5 sm:px-6 flex items-center gap-2"
                variant="default"
                aria-label="Отправить ссылку"
              >
                <ArrowUpCircle className="h-5 w-5" />
                Отправить
              </Button>
            </form>
            {submitted ? (
              <div className="mt-4 text-sm text-green-700 flex items-center gap-2">
                Доступ к разделам открыт.
              </div>
            ) : (
              <div className="mt-4 text-sm text-muted-foreground">
                После отправки ссылки станет доступна навигация по остальным разделам.
              </div>
            )}
          </main>
        </div>
      </div>
    </AuthGuard>
  )
}

