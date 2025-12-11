import { Bell } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

const navItems = [
  { name: "Import", active: false },
  { name: "Dashboard", active: true },
  { name: "Segments", active: false },
  { name: "Products", active: false },
  { name: "Reviews", active: false },
]

export function DashboardHeader() {
  return (
    <div className="flex justify-center">
      <header className="flex items-center justify-between bg-white rounded-full px-4 py-3 w-full max-w-[1292px]">
        <div className="w-10" /> {/* Spacer for balance */}
        <nav className="flex items-center gap-3 rounded-full bg-[#f0f0f0] px-5 py-2">
          {navItems.map((item) => (
            <button
              key={item.name}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                item.active ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {item.name}
            </button>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <button className="rounded-full p-2 hover:bg-muted">
            <Bell className="h-5 w-5" />
          </button>
          <Avatar className="h-10 w-10 bg-foreground">
            <AvatarImage src="/dark-avatar.png" />
            <AvatarFallback className="bg-foreground text-background">U</AvatarFallback>
          </Avatar>
        </div>
      </header>
    </div>
  )
}
