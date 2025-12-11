const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5000"

type ApiError = { success?: boolean; error?: string; message?: string }

export type AuthUser = {
  id: number
  username: string
  email: string
}

export type AuthSession = {
  token: string
  user: AuthUser
}

type AuthApiResponse = ApiError & {
  token?: string
  user?: AuthUser
  user_id?: number
  username?: string
  email?: string
}

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

const AUTH_TOKEN_KEY = "auth_token"
const AUTH_USER_KEY = "auth_user"

function ensureLeadingSlash(path: string) {
  return path.startsWith("/") ? path : `/${path}`
}

function buildHeaders(token?: string, headers?: HeadersInit): HeadersInit {
  const baseHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  }

  if (token) {
    baseHeaders.Authorization = `Bearer ${token}`
  }

  return {
    ...baseHeaders,
    ...(headers as Record<string, string>),
  }
}

export function getApiBaseUrl() {
  return API_BASE_URL
}

async function apiFetch<T>(
  path: string,
  options: RequestInit & { method?: HttpMethod; token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = options
  const url = `${API_BASE_URL}${ensureLeadingSlash(path)}`

  const response = await fetch(url, {
    cache: "no-store",
    ...rest,
    headers: buildHeaders(token, headers),
  })

  let data: unknown = null
  try {
    data = await response.json()
  } catch {
    // ignore json parsing errors, handle below
  }

  if (!response.ok) {
    const apiError = data as ApiError | null
    const message = apiError?.error || apiError?.message || `Ошибка ${response.status}`
    throw new Error(message)
  }

  if (data === null) {
    throw new Error("Пустой ответ от сервера")
  }

  return data as T
}

export async function registerUser(payload: {
  username: string
  email: string
  password: string
}): Promise<AuthSession> {
  const data = await apiFetch<AuthApiResponse>("/register", {
    method: "POST",
    body: JSON.stringify(payload),
  })

  if (!data.token) {
    throw new Error(data.error || data.message || "Не удалось получить токен")
  }

  return {
    token: data.token,
    user: data.user ?? {
      id: data.user_id ?? 0,
      username: data.username ?? payload.username,
      email: data.email ?? payload.email,
    },
  }
}

export async function loginUser(payload: {
  username: string
  password: string
}): Promise<AuthSession> {
  const data = await apiFetch<AuthApiResponse>("/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })

  if (!data.token || !data.user) {
    throw new Error(data.error || data.message || "Неверный ответ при входе")
  }

  return {
    token: data.token,
    user: data.user,
  }
}

export function saveAuthSession(session: AuthSession) {
  if (typeof window === "undefined") return
  localStorage.setItem(AUTH_TOKEN_KEY, session.token)
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(session.user))
}

export function clearAuthSession() {
  if (typeof window === "undefined") return
  localStorage.removeItem(AUTH_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
}

export function getAuthSession(): AuthSession | null {
  if (typeof window === "undefined") return null
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  const userRaw = localStorage.getItem(AUTH_USER_KEY)

  if (!token || !userRaw) return null

  try {
    const user = JSON.parse(userRaw) as AuthUser
    return { token, user }
  } catch {
    clearAuthSession()
    return null
  }
}

