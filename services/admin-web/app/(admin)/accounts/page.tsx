"use client"

import { useState, useEffect } from "react"
import { Search } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import type { Account } from "@/types/api"
import { format } from "date-fns"
import { ru } from "date-fns/locale"

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [filteredAccounts, setFilteredAccounts] = useState<Account[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    type: "all",
    status: "all",
    search: "",
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    filterAccounts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accounts, filters])

  const loadAccounts = async () => {
    try {
      setIsLoading(true)
      const data = await api.accounts.list()
      setAccounts(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки аккаунтов")
    } finally {
      setIsLoading(false)
    }
  }

  const filterAccounts = () => {
    let filtered = accounts

    if (filters.type !== "all") {
      filtered = filtered.filter((acc) => acc.type === filters.type)
    }

    if (filters.status !== "all") {
      filtered = filtered.filter((acc) => acc.status === filters.status)
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(
        (acc) =>
          acc.name.toLowerCase().includes(searchLower) ||
          acc.email.toLowerCase().includes(searchLower)
      )
    }

    setFilteredAccounts(filtered)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Аккаунты</h1>
        <p className="text-gray-500 mt-2">
          Управление пользователями и правами
        </p>
      </div>

      {error && (
        <div className="p-4 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Фильтры</CardTitle>
          <CardDescription>Фильтрация по типу, статусу или поиск</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Тип аккаунта</label>
              <Select
                value={filters.type}
                onValueChange={(value) => setFilters({ ...filters, type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Все типы" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все типы</SelectItem>
                  <SelectItem value="client">Клиент</SelectItem>
                  <SelectItem value="reseller">Реселлер</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Статус</label>
              <Select
                value={filters.status}
                onValueChange={(value) => setFilters({ ...filters, status: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Все статусы" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все статусы</SelectItem>
                  <SelectItem value="active">Активен</SelectItem>
                  <SelectItem value="suspended">Заблокирован</SelectItem>
                  <SelectItem value="inactive">Неактивен</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Поиск</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Поиск по имени или email..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="pl-8"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Список аккаунтов</CardTitle>
          <CardDescription>
            Показано {filteredAccounts.length} из {accounts.length} аккаунтов
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-gray-500">Загрузка аккаунтов...</p>
          ) : filteredAccounts.length === 0 ? (
            <p className="text-sm text-gray-500">Аккаунты не найдены</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Имя</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Баланс</TableHead>
                  <TableHead>SMS</TableHead>
                  <TableHead>Создан</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAccounts.map((account) => (
                  <TableRow key={account.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell className="font-medium">{account.name}</TableCell>
                    <TableCell>{account.email}</TableCell>
                    <TableCell>
                      <Badge variant={account.type === "reseller" ? "default" : "secondary"}>
                        {account.type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          account.status === "active"
                            ? "success"
                            : account.status === "suspended"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {account.status === "active" ? "Активен" : account.status === "suspended" ? "Заблокирован" : account.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{account.balance.toFixed(2)} UZS</TableCell>
                    <TableCell>{account.sms_count.toLocaleString()}</TableCell>
                    <TableCell>{format(new Date(account.created_at), "d MMM yyyy", { locale: ru })}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
