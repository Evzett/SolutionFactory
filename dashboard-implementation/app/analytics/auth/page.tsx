import { redirect } from "next/navigation"

export default function AnalyticsAuthRedirect() {
  redirect("/auth")
}

