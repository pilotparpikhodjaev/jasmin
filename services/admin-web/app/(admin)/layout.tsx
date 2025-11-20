"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuthStore } from "@/lib/stores/auth-store"
import { Button } from "@/components/ui/button"
import { LayoutDashboard, Users, Radio, CreditCard, Settings, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Обзор", href: "/admin", icon: LayoutDashboard },
  { name: "Операторы", href: "/admin/operators", icon: Radio },
  { name: "Аккаунты", href: "/admin/accounts", icon: Users },
  { name: "Биллинг", href: "/admin/billing", icon: CreditCard },
  { name: "Настройки", href: "/admin/settings", icon: Settings },
]

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { token, user, logout, fetchUser } = useAuthStore()
  const [isLoadingUser, setIsLoadingUser] = useState(false)

  useEffect(() => {
    if (!token) {
      router.push("/login")
      return
    }

    if (token && !user && !isLoadingUser) {
      setIsLoadingUser(true)
      fetchUser()
        .catch(() => {
          router.push("/login")
        })
        .finally(() => {
          setIsLoadingUser(false)
        })
    }
  }, [token, user, router, fetchUser, isLoadingUser])

  const handleLogout = async () => {
    await logout()
    router.push("/login")
  }

  if (!token) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex h-screen">
        <aside className="w-64 bg-white border-r border-gray-200">
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-center h-16 border-b border-gray-200">
              <h1 className="text-xl font-bold text-gray-900">Qalb SMS Admin</h1>
            </div>

            <nav className="flex-1 px-4 py-6 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    )}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            <div className="p-4 border-t border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">{user?.username || "Admin"}</p>
                  <p className="text-gray-500 text-xs">{user?.email || "administrator"}</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Выйти
              </Button>
            </div>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-6 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
