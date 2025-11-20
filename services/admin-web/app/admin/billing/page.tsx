"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Line, LineChart, CartesianGrid } from "recharts"
import { Download, Plus, CreditCard, FileText, Users, DollarSign, RefreshCw } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

// Mock Data for Analytics (Localized)
const revenueData = [
  { name: "Янв", revenue: 4000000, subscription: 2400000 },
  { name: "Фев", revenue: 3000000, subscription: 1398000 },
  { name: "Мар", revenue: 2000000, subscription: 9800000 },
  { name: "Апр", revenue: 2780000, subscription: 3908000 },
  { name: "Май", revenue: 1890000, subscription: 4800000 },
  { name: "Июн", revenue: 2390000, subscription: 3800000 },
]

const paymentTrendsData = [
  { date: "01.01", successful: 120, failed: 5 },
  { date: "02.01", successful: 132, failed: 3 },
  { date: "03.01", successful: 101, failed: 8 },
  { date: "04.01", successful: 134, failed: 2 },
  { date: "05.01", successful: 90, failed: 1 },
  { date: "06.01", successful: 230, failed: 10 },
  { date: "07.01", successful: 210, failed: 5 },
]

// Initial Invoice Data
const initialInvoices = [
  { id: "INV-001", customer: "OOO Acme Corp", amount: "2 500 000 UZS", status: "Paid", date: "15.01.2024" },
  { id: "INV-002", customer: "SP Globex", amount: "1 500 000 UZS", status: "Pending", date: "16.01.2024" },
  { id: "INV-003", customer: "IP Soylent", amount: "3 500 000 UZS", status: "Unpaid", date: "17.01.2024" },
]

// Operator Rates Data (Mock for now, usually fetched from backend)
const initialRates = [
  { id: 1, operator: "Ucell", code: "93, 94", price: 50.00, currency: "UZS" },
  { id: 2, operator: "Beeline", code: "90, 91", price: 50.00, currency: "UZS" },
  { id: 3, operator: "Mobiuz", code: "88, 97", price: 50.00, currency: "UZS" },
  { id: 4, operator: "Uztelecom", code: "99, 95", price: 45.00, currency: "UZS" },
  { id: 5, operator: "Humans", code: "33", price: 50.00, currency: "UZS" },
]

export default function AdminBillingPage() {
  const [invoices, setInvoices] = useState(initialInvoices)
  const [rates, setRates] = useState(initialRates)
  const [isGenerateOpen, setIsGenerateOpen] = useState(false)
  const [newInvoice, setNewInvoice] = useState({
    customer: "",
    amount: "",
    status: "Pending",
  })

  // Format currency
  const formatUZS = (amount: number) => {
    return new Intl.NumberFormat('ru-UZ', { style: 'currency', currency: 'UZS' }).format(amount)
  }

  const handleGenerateInvoice = () => {
    if (!newInvoice.customer || !newInvoice.amount) return

    const amountNum = parseFloat(newInvoice.amount)
    const invoice = {
      id: `INV-${String(invoices.length + 1).padStart(3, "0")}`,
      customer: newInvoice.customer,
      amount: formatUZS(isNaN(amountNum) ? 0 : amountNum),
      status: newInvoice.status,
      date: new Date().toLocaleDateString('ru-UZ'),
    }

    setInvoices([invoice, ...invoices])
    setIsGenerateOpen(false)
    setNewInvoice({ customer: "", amount: "", status: "Pending" })
  }

  const handleRateChange = (id: number, newPrice: string) => {
    const updatedRates = rates.map(rate => 
      rate.id === id ? { ...rate, price: parseFloat(newPrice) || 0 } : rate
    )
    setRates(updatedRates)
  }

  const saveRates = () => {
    // In a real app, this would PUT to /api/v1/payment/rates/{id}
    alert("Тарифы успешно сохранены!")
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Биллинг и Счета</h2>
        <div className="flex items-center space-x-2">
          <Button>
            <Download className="mr-2 h-4 w-4" />
            Скачать Отчет
          </Button>
        </div>
      </div>
      <Tabs defaultValue="analytics" className="space-y-4">
        <TabsList>
          <TabsTrigger value="analytics">Аналитика</TabsTrigger>
          <TabsTrigger value="invoices">Счета</TabsTrigger>
          <TabsTrigger value="configuration">Конфигурация</TabsTrigger>
        </TabsList>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Общий доход</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">45 231 890 UZS</div>
                <p className="text-xs text-muted-foreground">+20.1% с прошлого месяца</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Подписки</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">+2350</div>
                <p className="text-xs text-muted-foreground">+180.1% с прошлого месяца</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Активные Счета</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">+12 234</div>
                <p className="text-xs text-muted-foreground">+19% с прошлого месяца</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Ср. чек</CardTitle>
                <CreditCard className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">42 500 UZS</div>
                <p className="text-xs text-muted-foreground">+4% с прошлого месяца</p>
              </CardContent>
            </Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Обзор доходов</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={revenueData}>
                    <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                    <Tooltip formatter={(value: number) => formatUZS(value)} />
                    <Bar dataKey="revenue" fill="#adfa1d" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Тренды платежей</CardTitle>
                <CardDescription>Успешные vs Неуспешные за 7 дней</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={paymentTrendsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" fontSize={12} />
                    <Tooltip />
                    <Line type="monotone" dataKey="successful" stroke="#adfa1d" strokeWidth={2} name="Успешно" />
                    <Line type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={2} name="Ошибка" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Invoices Tab */}
        <TabsContent value="invoices" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Счета на оплату</CardTitle>
                <CardDescription>Управление счетами клиентов.</CardDescription>
              </div>
              <Dialog open={isGenerateOpen} onOpenChange={setIsGenerateOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" /> Создать Счет
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                  <DialogHeader>
                    <DialogTitle>Создать Счет</DialogTitle>
                    <DialogDescription>
                      Введите данные для нового счета. Нажмите создать.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="customer" className="text-right">
                        Клиент
                      </Label>
                      <Input
                        id="customer"
                        value={newInvoice.customer}
                        onChange={(e) => setNewInvoice({ ...newInvoice, customer: e.target.value })}
                        className="col-span-3"
                        placeholder="Например: OOO Acme"
                      />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="amount" className="text-right">
                        Сумма (UZS)
                      </Label>
                      <Input
                        id="amount"
                        type="number"
                        value={newInvoice.amount}
                        onChange={(e) => setNewInvoice({ ...newInvoice, amount: e.target.value })}
                        className="col-span-3"
                        placeholder="0"
                      />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="status" className="text-right">
                        Статус
                      </Label>
                      <Select
                        value={newInvoice.status}
                        onValueChange={(value) => setNewInvoice({ ...newInvoice, status: value })}
                      >
                        <SelectTrigger className="col-span-3">
                          <SelectValue placeholder="Выберите статус" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Pending">Ожидает</SelectItem>
                          <SelectItem value="Paid">Оплачен</SelectItem>
                          <SelectItem value="Unpaid">Не оплачен</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={handleGenerateInvoice}>Создать</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">№ Счета</TableHead>
                    <TableHead>Клиент</TableHead>
                    <TableHead>Дата</TableHead>
                    <TableHead>Сумма</TableHead>
                    <TableHead>Статус</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoices.map((invoice) => (
                    <TableRow key={invoice.id}>
                      <TableCell className="font-medium">{invoice.id}</TableCell>
                      <TableCell>{invoice.customer}</TableCell>
                      <TableCell>{invoice.date}</TableCell>
                      <TableCell>{invoice.amount}</TableCell>
                      <TableCell>
                        <Badge variant={invoice.status === "Paid" ? "secondary" : invoice.status === "Pending" ? "outline" : "destructive"}>
                          {invoice.status === "Paid" ? "Оплачен" : invoice.status === "Pending" ? "Ожидает" : "Не оплачен"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm">Просмотр</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Платежные Шлюзы</CardTitle>
                <CardDescription>Настройка провайдеров (Uzbekistan).</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="provider">Провайдер</Label>
                  <Select defaultValue="click">
                    <SelectTrigger id="provider">
                      <SelectValue placeholder="Выберите провайдера" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="click">Click (click.uz)</SelectItem>
                      <SelectItem value="payme">Payme (paycom.uz)</SelectItem>
                      <SelectItem value="uzum">Uzum Pay</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="merchant-id">Merchant ID</Label>
                  <Input id="merchant-id" type="password" value="mock_merchant_id" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secret-key">Secret Key</Label>
                  <Input id="secret-key" type="password" value="mock_secret_key" />
                </div>
                <Button>Сохранить настройки</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Настройки Счетов</CardTitle>
                <CardDescription>Налоги и валюта.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="tax-rate">НДС (%)</Label>
                  <Input id="tax-rate" type="number" defaultValue="12" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="currency">Валюта по умолчанию</Label>
                  <Select defaultValue="uzs">
                    <SelectTrigger id="currency">
                      <SelectValue placeholder="Выберите валюту" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="uzs">UZS (Сум)</SelectItem>
                      <SelectItem value="usd">USD ($)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button variant="outline">Обновить</Button>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Тарификация SMS (UZS)</CardTitle>
                <CardDescription>Базовые ставки по операторам Узбекистана.</CardDescription>
              </CardHeader>
              <CardContent>
                 <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Оператор</TableHead>
                      <TableHead>Коды (Prefix)</TableHead>
                      <TableHead>Цена за SMS (UZS)</TableHead>
                      <TableHead className="text-right">Действия</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rates.map((rate) => (
                      <TableRow key={rate.id}>
                        <TableCell className="font-medium">{rate.operator}</TableCell>
                        <TableCell>{rate.code}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Input 
                                className="w-24 h-8" 
                                type="number"
                                value={rate.price} 
                                onChange={(e) => handleRateChange(rate.id, e.target.value)}
                            />
                            <span className="text-xs text-muted-foreground">UZS</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                           <Button size="sm" variant="ghost">История</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 flex justify-end">
                    <Button onClick={saveRates}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Обновить Тарифы
                    </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
