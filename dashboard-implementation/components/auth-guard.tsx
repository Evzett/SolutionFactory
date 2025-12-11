"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { getAuthSession } from "@/lib/api"
import { Spinner } from "@/components/ui/spinner"

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    const session = getAuthSession()
    if (!session?.token) {
      router.replace("/auth")
      return
    }
    setChecked(true)
  }, [router])

  if (!checked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    )
  }

  return <>{children}</>
}

