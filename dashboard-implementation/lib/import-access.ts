const IMPORT_ACCESS_KEY = "import_access_granted"
const IMPORT_ACCESS_EVENT = "import-access-changed"

export function hasImportAccess() {
  if (typeof window === "undefined") return false
  return window.localStorage.getItem(IMPORT_ACCESS_KEY) === "true"
}

export function setImportAccess(granted: boolean) {
  if (typeof window === "undefined") return
  if (granted) {
    window.localStorage.setItem(IMPORT_ACCESS_KEY, "true")
  } else {
    window.localStorage.removeItem(IMPORT_ACCESS_KEY)
  }

  window.dispatchEvent(
    new CustomEvent(IMPORT_ACCESS_EVENT, {
      detail: { granted },
    }),
  )
}

export function onImportAccessChange(callback: (granted: boolean) => void) {
  if (typeof window === "undefined") return () => {}

  const handleStorage = (event: StorageEvent) => {
    if (event.key === IMPORT_ACCESS_KEY) {
      callback(event.newValue === "true")
    }
  }

  const handleCustom = (event: Event) => {
    const detail = (event as CustomEvent<{ granted: boolean }>).detail
    if (typeof detail?.granted === "boolean") {
      callback(detail.granted)
    } else {
      callback(hasImportAccess())
    }
  }

  window.addEventListener("storage", handleStorage)
  window.addEventListener(IMPORT_ACCESS_EVENT, handleCustom)

  return () => {
    window.removeEventListener("storage", handleStorage)
    window.removeEventListener(IMPORT_ACCESS_EVENT, handleCustom)
  }
}

