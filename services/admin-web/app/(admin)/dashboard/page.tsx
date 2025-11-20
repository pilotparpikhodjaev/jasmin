"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Users, Radio, MessageSquare, DollarSign } from "lucide-react"

const stats = [
  {
    name: "Аккаунты",
    value: "0",
    icon: Users,
    description: "Активные пользователи",
  },
  {
    name: "Операторы",
    value: "0",
    icon: Radio,
    description: "Подключенные SMSC",
  },
  {
    name: "Сообщений сегодня",
    value: "0",
    icon: MessageSquare,
    description: "Всего отправлено",
  },
  {
    name: "Доход",
    value: "0 UZS",
    icon: DollarSign,
    description: "Выручка за месяц",
  },
]

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Обзор платформы</h1>
        <p className="text-gray-500 mt-2">
          Мониторинг SMS-шлюза
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.name}
                </CardTitle>
                <Icon className="h-4 w-4 text-gray-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-gray-500 mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Последние действия</CardTitle>
            <CardDescription>События системы</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">Нет последних действий</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Состояние системы</CardTitle>
            <CardDescription>Метрики платформы</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">API Статус</span>
                <span className="text-sm font-medium text-green-600">Работает</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Очередь (RabbitMQ)</span>
                <span className="text-sm font-medium text-green-600">Норма</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">База Данных</span>
                <span className="text-sm font-medium text-green-600">Подключено</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
