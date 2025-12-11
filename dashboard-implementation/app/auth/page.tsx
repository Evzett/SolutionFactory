"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { getApiBaseUrl, getAuthSession, loginUser, registerUser, saveAuthSession } from "@/lib/api"

const registerSchema = z.object({
  username: z
    .string()
    .trim()
    .min(3, "Минимум 3 символа")
    .max(50, "Не более 50 символов")
    .regex(/^[\w.-]+$/, "Можно использовать буквы, цифры, точку, дефис и подчеркивание"),
  email: z.string().trim().email("Введите корректный email"),
  password: z.string().min(6, "Минимум 6 символов"),
})

const loginSchema = z.object({
  username: z.string().trim().min(1, "Введите логин или email"),
  password: z.string().min(6, "Минимум 6 символов"),
})

type RegisterFormValues = z.infer<typeof registerSchema>
type LoginFormValues = z.infer<typeof loginSchema>

type Status = { type: "success" | "error"; message: string } | null

export default function AuthPage() {
  const router = useRouter()
  const [status, setStatus] = useState<Status>(null)
  const [activeTab, setActiveTab] = useState<"login" | "register">("login")
  const [loading, setLoading] = useState<"login" | "register" | null>(null)

  const registerForm = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", email: "", password: "" },
  })

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  })

  useEffect(() => {
    const session = getAuthSession()
    if (session?.token) {
      router.replace("/")
    }
  }, [router])

  const handleRegister = async (values: RegisterFormValues) => {
    setStatus(null)
    setLoading("register")
    try {
      const session = await registerUser(values)
      saveAuthSession(session)
      setStatus({ type: "success", message: "Регистрация успешна. Перенаправляем..." })
      router.push("/analytics")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Не удалось зарегистрироваться"
      setStatus({ type: "error", message })
    } finally {
      setLoading(null)
    }
  }

  const handleLogin = async (values: LoginFormValues) => {
    setStatus(null)
    setLoading("login")
    try {
      const session = await loginUser(values)
      saveAuthSession(session)
      setStatus({ type: "success", message: "Вход выполнен. Перенаправляем..." })
      router.push("/analytics")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Не удалось войти"
      setStatus({ type: "error", message })
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4 py-10">
      <Card className="w-full max-w-xl">
        <CardHeader className="space-y-2">
          <CardTitle className="text-2xl">Войдите или создайте аккаунт</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {status ? (
            <Alert variant={status.type === "error" ? "destructive" : "default"}>
              <AlertTitle>{status.type === "error" ? "Ошибка" : "Успех"}</AlertTitle>
              <AlertDescription>{status.message}</AlertDescription>
            </Alert>
          ) : null}

          <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as typeof activeTab)}>
            <TabsList className="mb-4">
              <TabsTrigger value="login">Вход</TabsTrigger>
              <TabsTrigger value="register">Регистрация</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form
                className="space-y-4"
                onSubmit={loginForm.handleSubmit(handleLogin)}
                noValidate
              >
                <div className="space-y-2">
                  <Label htmlFor="login-username">Логин или email</Label>
                  <Input
                    id="login-username"
                    placeholder="username или email"
                    autoComplete="username"
                    {...loginForm.register("username")}
                  />
                  {loginForm.formState.errors.username ? (
                    <p className="text-sm text-destructive">
                      {loginForm.formState.errors.username.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="login-password">Пароль</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    {...loginForm.register("password")}
                  />
                  {loginForm.formState.errors.password ? (
                    <p className="text-sm text-destructive">
                      {loginForm.formState.errors.password.message}
                    </p>
                  ) : null}
                </div>

                <Button className="w-full" type="submit" disabled={loading === "login"}>
                  {loading === "login" ? "Входим..." : "Войти"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form
                className="space-y-4"
                onSubmit={registerForm.handleSubmit(handleRegister)}
                noValidate
              >
                <div className="space-y-2">
                  <Label htmlFor="reg-username">Имя пользователя</Label>
                  <Input
                    id="reg-username"
                    placeholder="username"
                    autoComplete="username"
                    {...registerForm.register("username")}
                  />
                  {registerForm.formState.errors.username ? (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.username.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-email">Email</Label>
                  <Input
                    id="reg-email"
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    {...registerForm.register("email")}
                  />
                  {registerForm.formState.errors.email ? (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.email.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-password">Пароль</Label>
                  <Input
                    id="reg-password"
                    type="password"
                    placeholder="••••••••"
                    autoComplete="new-password"
                    {...registerForm.register("password")}
                  />
                  {registerForm.formState.errors.password ? (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.password.message}
                    </p>
                  ) : null}
                </div>

                <Button className="w-full" type="submit" disabled={loading === "register"}>
                  {loading === "register" ? "Регистрируем..." : "Зарегистрироваться"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

