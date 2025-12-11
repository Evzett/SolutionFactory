"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Bell, DoorOpen, Settings, User } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { AuthSession, clearAuthSession, getAuthSession } from "@/lib/api"
import { hasImportAccess, onImportAccessChange, setImportAccess } from "@/lib/import-access"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const NAV_ITEMS = [
  { label: "Import", href: "/analytics" },
  { label: "Dashboard", href: "/" },
  { label: "Segments", href: "/segments" },
  { label: "Products", href: "/products" },
  { label: "Reviews", href: "/reviews" },
]

interface AppNavProps {
  className?: string
}

export function AppNav({ className }: AppNavProps) {
  const pathname = usePathname()
  const [session, setSession] = useState<AuthSession | null>(null)
  const [importReady, setImportReady] = useState(false)

  useEffect(() => {
    const currentSession = getAuthSession()
    setSession(currentSession)

    if (currentSession) {
      setImportReady(hasImportAccess())
    } else {
      setImportReady(false)
      setImportAccess(false)
    }

    const off = onImportAccessChange(setImportReady)
    return () => off()
  }, [])

  const handleLogout = () => {
    clearAuthSession()
    setSession(null)
    setImportReady(false)
    setImportAccess(false)
  }

  return (
    <div className={cn("w-full flex justify-center px-4 sm:px-6 lg:px-8", className)}>
      <div className="flex items-center justify-between bg-white rounded-full px-4 py-3 w-full max-w-[1292px]">
        <div className="w-10" />
        <nav className="flex items-center gap-3 rounded-full bg-[#f0f0f0] px-5 py-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href))
            const disabled = !importReady && item.href !== "/analytics"

            if (disabled) {
              return (
                <span
                  key={item.href}
                  className="rounded-full px-5 py-2 text-sm font-medium whitespace-nowrap text-muted-foreground/60 cursor-not-allowed select-none"
                  title="Доступ откроется после отправки ссылки на Import"
                >
                  {item.label}
                </span>
              )
            }

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-5 py-2 text-sm font-medium transition-colors whitespace-nowrap",
                  isActive ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="flex items-center gap-3">
          <button className="rounded-full p-2 hover:bg-muted" aria-label="Notifications">
            <Bell className="h-5 w-5" />
          </button>
          {session ? (
            <>
              <div className="hidden sm:flex flex-col items-end text-sm leading-tight">
                <span className="font-semibold">{session.user.username}</span>
                <span className="text-muted-foreground">{session.user.email}</span>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button aria-label="Открыть меню профиля">
                    <Avatar className="h-10 w-10 bg-foreground">
                      <AvatarImage src="/dark-avatar.png" alt="User avatar" loading="eager" />
                      <AvatarFallback className="bg-foreground text-background" aria-hidden>
                        {/* empty to avoid flash of fallback letter */}
                      </AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52">
                  <DropdownMenuLabel className="flex flex-col">
                    <span className="font-semibold">{session.user.username}</span>
                    <span className="text-xs text-muted-foreground">{session.user.email}</span>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <User className="h-4 w-4 mr-2" />
                    Профиль
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="h-4 w-4 mr-2" />
                    Настройки
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                    <DoorOpen className="h-4 w-4 mr-2" />
                    Выйти
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}

