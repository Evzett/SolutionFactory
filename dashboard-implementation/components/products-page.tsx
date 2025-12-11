"use client"

import type React from "react"

import { useState, useRef, useMemo, useEffect } from "react"
import { Star, ArrowUpRight, Search, X, ExternalLink, Upload, Sparkles, Pencil, Check, Plus, Trash2, Sparkles as SparklesIcon, Copy, Loader2, AlertTriangle } from "lucide-react"
import { AppNav } from "@/components/app-nav"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"
import { getAuthSession } from "@/lib/api"

interface Product {
  id: number
  name: string
  rating: string
  article: string
  shortDescription: string
  fullDescription: string
  bulletPoints: string[]
  price: string
  image: string
  characteristics: {
    label: string
    value: string
  }[]
}

const products: Product[] = [
  {
    id: 1,
    name: "ЛОФЕРЫ LOOKING.SHIK С РЕМЕШКОМ БЕЗ КАБЛУКА",
    rating: "4,9+",
    article: "2452668125",
    shortDescription: "ЭЛЕГАНТНЫЕ ЛОФЕРЫ С РЕМЕШКОМ ДЛЯ ПОВСЕДНЕВНОЙ НОСКИ В КЛАССИЧЕСКОМ СТИЛЕ",
    fullDescription: "ЭЛЕГАНТНЫЕ ЛОФЕРЫ С РЕМЕШКОМ ДЛЯ ПОВСЕДНЕВНОЙ НОСКИ В КЛАССИЧЕСКОМ СТИЛЕ. ИДЕАЛЬНО ПОДХОДЯТ ДЛЯ ОФИСА И ПОВСЕДНЕВНОЙ НОСКИ",
    bulletPoints: [
      "Классический дизайн с ремешком",
      "Удобная посадка",
      "Универсальный стиль",
    ],
    price: "2592 ₽",
    image: "/Лоферы LOOKING.SHIK лоферы с ремешком без каблука.jpg",
    characteristics: [
      { label: "МАТЕРИАЛ ПОДОШВЫ", value: "ПВХ (поливинилхлорид), Термопластичная резина (ТПР)" },
      { label: "ВЫСОТА КАБЛУКА", value: "2 см" },
      { label: "СЕЗОН", value: "На любой сезон" },
      { label: "ЦВЕТ", value: "Черный лак" },
      { label: "РОССИЙСКИЙ РАЗМЕР", value: "36, 37, 38, 39, 40, 41" },
    ],
  },
  {
    id: 2,
    name: "ЛОФЕРЫ LOOKING.SHIK С РЕМЕШКОМ БЕЗ КАБЛУКА",
    rating: "4,9+",
    article: "2625598176",
    shortDescription: "СТИЛЬНЫЕ ЛОФЕРЫ БОРДОВОГО ЦВЕТА С РЕМЕШКОМ ДЛЯ СОВРЕМЕННОГО ОБРАЗА",
    fullDescription: "СТИЛЬНЫЕ ЛОФЕРЫ БОРДОВОГО ЦВЕТА С РЕМЕШКОМ ДЛЯ СОВРЕМЕННОГО ОБРАЗА. ОТЛИЧНО КОМБИНИРУЮТСЯ С РАЗЛИЧНЫМИ СТИЛЯМИ ОДЕЖДЫ",
    bulletPoints: [
      "Бордовый цвет",
      "Классический дизайн",
      "Комфортная носка",
    ],
    price: "2615 ₽",
    image: "/Лоферы LOOKING.SHIK лоферы с ремешком без каблука (2).jpg",
    characteristics: [
      { label: "МАТЕРИАЛ ПОДОШВЫ", value: "ПВХ (поливинилхлорид), Термопластичная резина (ТПР)" },
      { label: "СЕЗОН", value: "На любой сезон" },
      { label: "ЦВЕТ", value: "Бордо" },
      { label: "РОССИЙСКИЙ РАЗМЕР", value: "36, 37, 38, 39, 40, 41" },
    ],
  },
  {
    id: 3,
    name: "КРОССОВКИ LOOKING.SHIK",
    rating: "4,9+",
    article: "1352515118",
    shortDescription: "УНИВЕРСАЛЬНЫЕ КРОССОВКИ ДЛЯ БЕГА, ЙОГИ И СПОРТИВНОЙ ХОДЬБЫ",
    fullDescription: "УНИВЕРСАЛЬНЫЕ КРОССОВКИ ДЛЯ БЕГА, ЙОГИ И СПОРТИВНОЙ ХОДЬБЫ. ОТЛИЧНО ПОДХОДЯТ ДЛЯ АКТИВНОГО ОБРАЗА ЖИЗНИ И ТРЕНИРОВОК",
    bulletPoints: [
      "Вспененный полимер для амортизации",
      "Дышащие материалы",
      "Универсальное спортивное назначение",
    ],
    price: "1695 ₽",
    image: "/Кроссовки LOOKING.SHIK.jpg",
    characteristics: [
      { label: "МАТЕРИАЛ", value: "Искусственные материалы" },
      { label: "МАТЕРИАЛ СТЕЛЬКИ", value: "Искусственные материалы" },
      { label: "МАТЕРИАЛ ПОДОШВЫ", value: "Вспененный полимер" },
      { label: "СПОРТИВНОЕ НАЗНАЧЕНИЕ", value: "Бег, Йога и пилатес, Спортивная ходьба" },
      { label: "СЕЗОН", value: "На любой сезон" },
      { label: "РОССИЙСКИЙ РАЗМЕР", value: "35, 36, 37, 38, 39, 40, 41" },
    ],
  },
]

export function ProductsPage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [editedData, setEditedData] = useState<{
    image: string
    description: string
    bulletPoints: string[]
    characteristics: { label: string; value: string }[]
  } | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isPublished, setIsPublished] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [shopUrl, setShopUrl] = useState("")
  const [currentUserId, setCurrentUserId] = useState<number | null>(null)

  // Загружаем состояние магазина для текущего пользователя
  useEffect(() => {
    const session = getAuthSession()
    if (session?.user?.id) {
      setCurrentUserId(session.user.id)
      const publishedKey = `shop_published_${session.user.id}`
      const urlKey = `personal_shop_url_${session.user.id}`
      
      const published = localStorage.getItem(publishedKey) === "true"
      const url = localStorage.getItem(urlKey) || ""
      
      setIsPublished(published)
      setShopUrl(url)
      
      // Симулируем загрузку магазина
      setTimeout(() => {
        setIsLoading(false)
      }, 1500)
    } else {
      setIsLoading(false)
    }
  }, [])

  const handlePublishClick = () => {
    setShowConfirmDialog(true)
  }

  const handleConfirmPublish = async () => {
    if (!currentUserId) return
    
    setShowConfirmDialog(false)
    
    // Генерируем уникальный URL для магазина
    const session = getAuthSession()
    const username = session?.user?.username || "user"
    const uniqueId = Math.random().toString(36).substring(2, 9)
    const generatedUrl = `https://shop.example.com/${username}-${uniqueId}`
    
    setShopUrl(generatedUrl)
    setIsPublished(true)
    
    // Сохраняем состояние для конкретного пользователя
    const publishedKey = `shop_published_${currentUserId}`
    const urlKey = `personal_shop_url_${currentUserId}`
    localStorage.setItem(publishedKey, "true")
    localStorage.setItem(urlKey, generatedUrl)
    
    toast.success("Персональный магазин опубликован!", {
      description: "Теперь данные нельзя изменить. Вы можете поделиться ссылкой с клиентами.",
      duration: 5000,
    })
  }

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(shopUrl)
      toast.success("Ссылка скопирована", {
        description: "Ссылка на ваш магазин скопирована в буфер обмена.",
      })
    } catch (err) {
      toast.error("Не удалось скопировать", {
        description: "Попробуйте скопировать ссылку вручную.",
      })
    }
  }

  const filteredProducts = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()
    if (!query) return products

    return products.filter((product) => {
      const haystack = [
        product.name,
        product.article,
        product.shortDescription,
        product.fullDescription,
        ...product.bulletPoints,
        ...product.characteristics.map((c) => `${c.label} ${c.value}`),
      ]
        .join(" ")
        .toLowerCase()

      return haystack.includes(query)
    })
  }, [searchQuery])

  const handleOpenModal = (product: Product) => {
    setSelectedProduct(product)
    setEditedData({
      image: product.image,
      description: product.fullDescription,
      bulletPoints: [...product.bulletPoints],
      characteristics: [...product.characteristics],
    })
  }

  const handleCloseModal = () => {
    setSelectedProduct(null)
    setEditedData(null)
  }

  return (
    <div className="min-h-screen bg-[#f5f5f5] flex flex-col items-center pt-6 sm:pt-8 lg:pt-10 px-6 pb-6 gap-6">
      <AppNav />

      {/* Content Area */}
      <div className="w-full max-w-[1292px] flex flex-col gap-6">
        {/* Title */}
        <div className="flex items-center justify-between gap-6">
          <h1 className="text-xl font-bold tracking-tight">ВАШ ПЕРСОНАЛЬНЫЙ ИНТЕРНЕТ-МАГАЗИН ГОТОВ!</h1>
          {!isPublished && (
            <Button
              onClick={handlePublishClick}
              className="rounded-full uppercase font-semibold bg-foreground text-background hover:bg-foreground/90 shrink-0"
            >
              <SparklesIcon className="h-4 w-4 mr-2" />
              Создать персональный магазин
            </Button>
          )}
        </div>

        {/* Search Bar and Shop URL Row */}
        <div className="flex items-center justify-between gap-4">
          {/* Search Bar */}
          <div className="flex-1 max-w-sm">
            <div className="relative">
              <input
                type="text"
                placeholder="Поиск товаров"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white rounded-full h-10 px-5 pr-12 outline-none text-sm"
                disabled={isLoading}
              />
              <button className="absolute right-3 top-1/2 -translate-y-1/2 p-1">
                <Search className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          </div>

          {/* Shop URL - показываем на уровне с поиском */}
          {isPublished && shopUrl && (
            <div className="flex items-center gap-2 bg-white rounded-full h-10 px-4 border border-border">
              <span className="text-sm text-muted-foreground truncate max-w-[300px]">{shopUrl}</span>
              <button
                onClick={handleCopyUrl}
                className="p-1.5 hover:bg-muted rounded-full transition-colors shrink-0"
                title="Скопировать ссылку"
              >
                <Copy className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          )}
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <Loader2 className="h-12 w-12 animate-spin text-foreground" />
            <p className="text-muted-foreground">Загрузка магазина...</p>
          </div>
        ) : (
          /* Product Cards Grid */
          filteredProducts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} onClick={() => handleOpenModal(product)} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-3xl p-8 text-center text-muted-foreground">
              Ничего не найдено по запросу "{searchQuery}"
            </div>
          )
        )}
      </div>

      {/* Modal Overlay */}
      {selectedProduct && editedData && (
        <ProductModal
          product={selectedProduct}
          editedData={editedData}
          setEditedData={setEditedData}
          onClose={handleCloseModal}
          isReadOnly={isPublished}
        />
      )}

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent className="sm:max-w-[650px] rounded-3xl border-2 p-6 sm:p-8">
          <DialogHeader className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-yellow-500/10 rounded-2xl shrink-0">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
              </div>
              <DialogTitle className="text-2xl font-bold uppercase tracking-tight">
                Вы уверены?
              </DialogTitle>
            </div>
            <DialogDescription className="text-base text-muted-foreground leading-relaxed">
              После создания персонального магазина вы <span className="font-semibold text-foreground">не сможете изменить данные</span> товаров.
              <br />
              <br />
              Убедитесь, что все карточки товаров заполнены правильно перед публикацией.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="flex-col sm:flex-row gap-3 mt-6">
            <Button
              variant="outline"
              onClick={() => setShowConfirmDialog(false)}
              className="w-full sm:flex-1 rounded-full uppercase font-semibold text-xs sm:text-sm px-4 sm:px-6 py-2.5 min-w-0"
            >
              Нет, вернуться к редактированию
            </Button>
            <Button
              onClick={handleConfirmPublish}
              className="w-full sm:flex-1 rounded-full uppercase font-semibold bg-foreground text-background hover:bg-foreground/90 text-xs sm:text-sm px-4 sm:px-6 py-2.5 min-w-0"
            >
              Да, создать магазин
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ProductCard({
  product,
  onClick,
}: {
  product: Product
  onClick: () => void
}) {
  return (
    <div onClick={onClick} className="bg-white rounded-3xl p-6 cursor-pointer hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-[15px] leading-none uppercase mb-2">{product.name}</h3>
          <div className="flex items-center gap-2 text-sm">
            <Star className="h-4 w-4 fill-foreground" />
            <span>{product.rating}</span>
            <span className="text-muted-foreground uppercase">АРТИКУЛ: {product.article}</span>
          </div>
        </div>
        <button className="p-2 hover:bg-muted rounded-full">
          <ArrowUpRight className="h-5 w-5" />
        </button>
      </div>

      {/* Image */}
      <div className="bg-foreground rounded-2xl aspect-[4/3] mb-4 overflow-hidden">
        <img src={product.image || "/placeholder.svg"} alt={product.name} className="w-full h-full object-cover scale-110" />
      </div>

      {/* Description */}
      <p className="text-sm font-medium mb-4 leading-relaxed uppercase">{product.shortDescription}</p>

      {/* Price */}
      <p className="text-3xl font-bold text-right">{product.price}</p>
    </div>
  )
}

function ProductModal({
  product,
  editedData,
  setEditedData,
  onClose,
  isReadOnly = false,
}: {
  product: Product
  editedData: {
    image: string
    description: string
    bulletPoints: string[]
    characteristics: { label: string; value: string }[]
  }
  setEditedData: (data: {
    image: string
    description: string
    bulletPoints: string[]
    characteristics: { label: string; value: string }[]
  }) => void
  onClose: () => void
  isReadOnly?: boolean
}) {
  const [showImageMenu, setShowImageMenu] = useState(false)
  const [isEditingDescription, setIsEditingDescription] = useState(false)
  const [editingBulletIndex, setEditingBulletIndex] = useState<number | null>(null)
  const [editingCharIndex, setEditingCharIndex] = useState<number | null>(null)
  const [isAiProcessing, setIsAiProcessing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const url = URL.createObjectURL(file)
      setEditedData({ ...editedData, image: url })
      setShowImageMenu(false)
    }
  }

  const handleAiEnhance = () => {
    setIsAiProcessing(true)
    setTimeout(() => {
      setIsAiProcessing(false)
      setShowImageMenu(false)
    }, 2000)
  }

  const updateBulletPoint = (index: number, value: string) => {
    const newBullets = [...editedData.bulletPoints]
    newBullets[index] = value
    setEditedData({ ...editedData, bulletPoints: newBullets })
  }

  const addBulletPoint = () => {
    setEditedData({
      ...editedData,
      bulletPoints: [...editedData.bulletPoints, "Новый признак"],
    })
    setEditingBulletIndex(editedData.bulletPoints.length)
  }

  const removeBulletPoint = (index: number) => {
    const newBullets = editedData.bulletPoints.filter((_, i) => i !== index)
    setEditedData({ ...editedData, bulletPoints: newBullets })
    setEditingBulletIndex(null)
  }

  const updateCharacteristic = (index: number, field: "label" | "value", value: string) => {
    const newChars = [...editedData.characteristics]
    newChars[index] = { ...newChars[index], [field]: value }
    setEditedData({ ...editedData, characteristics: newChars })
  }

  const addCharacteristic = () => {
    setEditedData({
      ...editedData,
      characteristics: [...editedData.characteristics, { label: "НОВАЯ", value: "значение" }],
    })
    setEditingCharIndex(editedData.characteristics.length)
  }

  const removeCharacteristic = (index: number) => {
    const newChars = editedData.characteristics.filter((_, i) => i !== index)
    setEditedData({ ...editedData, characteristics: newChars })
    setEditingCharIndex(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4 py-8" onClick={onClose}>
      {/* Backdrop with blur */}
      <div className="absolute inset-0 bg-white/60 backdrop-blur-sm" />

      {/* Modal Content */}
      <div
        className="relative bg-white rounded-3xl p-8 w-full max-w-5xl max-h-full overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button onClick={onClose} className="absolute top-6 right-6 p-2 hover:bg-muted rounded-full z-10">
          <X className="h-5 w-5" />
        </button>

        {/* Modal Content Layout */}
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div className="mb-2">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="font-semibold text-[15px] leading-none uppercase">{product.name}</h2>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Star className="h-5 w-5 fill-foreground" />
              <span>{product.rating}</span>
              <span className="text-muted-foreground uppercase">АРТИКУЛ: {product.article}</span>
            </div>
          </div>

          {/* Image */}
          <div className="relative w-full">
            <div className="bg-foreground rounded-2xl aspect-[16/9] w-full overflow-hidden">
              <img
                src={editedData.image || "/placeholder.svg"}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            </div>
            {!isReadOnly && (
              <>
                <button
                  onClick={() => setShowImageMenu(!showImageMenu)}
                  className="absolute top-3 right-3 p-2 bg-white/80 hover:bg-white rounded-full transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                </button>
                {showImageMenu && (
                  <div className="absolute top-14 right-3 bg-white rounded-2xl shadow-lg p-2 min-w-[240px] z-20">
                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*" className="hidden" />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-3 w-full px-4 py-3 rounded-xl hover:bg-muted transition-colors text-left"
                    >
                      <Upload className="h-5 w-5" />
                      <span className="text-sm font-medium">Загрузить фото</span>
                    </button>
                    <button
                      onClick={handleAiEnhance}
                      disabled={isAiProcessing}
                      className="flex items-center gap-3 w-full px-4 py-3 rounded-xl hover:bg-muted transition-colors text-left disabled:opacity-50"
                    >
                      <Sparkles className="h-5 w-5" />
                      <span className="text-sm font-medium">
                        {isAiProcessing ? "Улучшаем..." : "Улучшить с помощью ИИ"}
                      </span>
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Description */}
          <div className="flex items-start gap-2">
            {!isReadOnly && isEditingDescription ? (
              <div className="flex-1 flex items-start gap-2">
                <textarea
                  value={editedData.description}
                  onChange={(e) => setEditedData({ ...editedData, description: e.target.value })}
                  className="flex-1 text-sm font-medium leading-relaxed uppercase bg-muted/50 rounded-xl p-3 outline-none resize-none min-h-[80px]"
                  autoFocus
                />
                <button
                  onClick={() => setIsEditingDescription(false)}
                  className="p-2 bg-foreground text-background rounded-full hover:bg-foreground/80 transition-colors shrink-0"
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <>
                <p className="text-sm font-medium leading-relaxed uppercase flex-1">{editedData.description}</p>
                {!isReadOnly && (
                  <button
                    onClick={() => setIsEditingDescription(true)}
                    className="p-2 hover:bg-muted rounded-full transition-colors shrink-0"
                  >
                    <Pencil className="h-4 w-4 text-muted-foreground" />
                  </button>
                )}
              </>
            )}
          </div>

          <div>
            <ul className="space-y-2 text-sm">
              {editedData.bulletPoints.map((point, index) => (
                <li key={index} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-foreground shrink-0" />
                  {!isReadOnly && editingBulletIndex === index ? (
                    <div className="flex-1 flex items-center gap-2">
                      <input
                        value={point}
                        onChange={(e) => updateBulletPoint(index, e.target.value)}
                        className="flex-1 text-sm uppercase bg-muted/50 rounded-lg px-3 py-2 outline-none"
                        autoFocus
                      />
                      <button
                        onClick={() => setEditingBulletIndex(null)}
                        className="p-1.5 bg-foreground text-background rounded-full hover:bg-foreground/80"
                      >
                        <Check className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => removeBulletPoint(index)}
                        className="p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-between group">
                      <span className="uppercase">{point}</span>
                      {!isReadOnly && (
                        <button
                          onClick={() => setEditingBulletIndex(index)}
                          className="p-1.5 hover:bg-muted rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Pencil className="h-3 w-3 text-muted-foreground" />
                        </button>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
            {!isReadOnly && (
              <button
                onClick={addBulletPoint}
                className="flex items-center gap-2 mt-3 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Добавить признак</span>
              </button>
            )}
          </div>

          <div>
            <h4 className="font-bold text-sm mb-3 uppercase">ХАРАКТЕРИСТИКИ</h4>
            <div className="space-y-2 text-sm">
              {editedData.characteristics.map((char, index) => (
                <div key={index} className="flex items-center gap-2">
                  {!isReadOnly && editingCharIndex === index ? (
                    <div className="flex-1 flex items-center gap-2">
                      <input
                        value={char.label}
                        onChange={(e) => updateCharacteristic(index, "label", e.target.value)}
                        className="w-32 text-sm uppercase font-medium bg-muted/50 rounded-lg px-3 py-2 outline-none"
                        placeholder="Название"
                      />
                      <span>:</span>
                      <input
                        value={char.value}
                        onChange={(e) => updateCharacteristic(index, "value", e.target.value)}
                        className="flex-1 text-sm bg-muted/50 rounded-lg px-3 py-2 outline-none"
                        placeholder="Значение"
                        autoFocus
                      />
                      <button
                        onClick={() => setEditingCharIndex(null)}
                        className="p-1.5 bg-foreground text-background rounded-full hover:bg-foreground/80"
                      >
                        <Check className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => removeCharacteristic(index)}
                        className="p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-between group">
                      <p>
                        <span className="font-medium uppercase">{char.label}:</span> {char.value}
                      </p>
                      {!isReadOnly && (
                        <button
                          onClick={() => setEditingCharIndex(index)}
                          className="p-1.5 hover:bg-muted rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Pencil className="h-3 w-3 text-muted-foreground" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
            {!isReadOnly && (
              <button
                onClick={addCharacteristic}
                className="flex items-center gap-2 mt-3 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Добавить характеристику</span>
              </button>
            )}
          </div>

          {/* Price */}
          <p className="text-5xl font-bold text-right mt-auto">{product.price}</p>
        </div>
      </div>
    </div>
  )
}
