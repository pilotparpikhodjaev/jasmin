"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Shield, Globe, Server, Bell, Save, AlertTriangle, Activity, Lock } from "lucide-react"

export default function AdminSettingsPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Настройки Платформы</h2>
          <p className="text-muted-foreground">
            Управление глобальной конфигурацией SMS-шлюза.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button>
            <Save className="mr-2 h-4 w-4" />
            Сохранить
          </Button>
        </div>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 lg:w-[600px]">
          <TabsTrigger value="general">Общие</TabsTrigger>
          <TabsTrigger value="gateway">Шлюз</TabsTrigger>
          <TabsTrigger value="security">Безопасность</TabsTrigger>
          <TabsTrigger value="notifications">Уведомления</TabsTrigger>
          <TabsTrigger value="system">Система</TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Идентификация Платформы
                </CardTitle>
                <CardDescription>Базовая информация о вашем SaaS.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="platform-name">Название платформы</Label>
                  <Input id="platform-name" defaultValue="Qalb SMS Gateway" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="support-email">Email поддержки</Label>
                  <Input id="support-email" defaultValue="support@qalb.uz" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="website">Веб-сайт</Label>
                  <Input id="website" defaultValue="https://sms.qalb.uz" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Локализация</CardTitle>
                <CardDescription>Настройки по умолчанию для пользователей.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="timezone">Часовой пояс</Label>
                  <Select defaultValue="uzt">
                    <SelectTrigger id="timezone">
                      <SelectValue placeholder="Выберите часовой пояс" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="utc">UTC (GMT+0)</SelectItem>
                      <SelectItem value="est">EST (GMT-5)</SelectItem>
                      <SelectItem value="uzt">UZT (GMT+5)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">Язык по умолчанию</Label>
                  <Select defaultValue="ru">
                    <SelectTrigger id="language">
                      <SelectValue placeholder="Выберите язык" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="ru">Русский</SelectItem>
                      <SelectItem value="uz">O&apos;zbekcha</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                 <div className="space-y-2">
                  <Label htmlFor="date-format">Формат даты</Label>
                  <Select defaultValue="iso">
                    <SelectTrigger id="date-format">
                      <SelectValue placeholder="Выберите формат" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="iso">ГГГГ-ММ-ДД</SelectItem>
                      <SelectItem value="us">ММ/ДД/ГГГГ</SelectItem>
                      <SelectItem value="eu">ДД.ММ.ГГГГ</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Gateway Settings - Core SaaS Logic */}
        <TabsContent value="gateway" className="space-y-4">
           <div className="grid gap-4 md:grid-cols-2">
             <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  Управление Трафиком
                </CardTitle>
                <CardDescription>Глобальные лимиты и пропускная способность.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="global-rps">Глобальный лимит (RPS)</Label>
                  <Input id="global-rps" type="number" defaultValue="500" />
                  <p className="text-xs text-muted-foreground">Максимум запросов в секунду для всей платформы.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max-parts">Макс. частей SMS</Label>
                  <Input id="max-parts" type="number" defaultValue="6" />
                  <p className="text-xs text-muted-foreground">Максимальное количество сегментов в одном сообщении.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="burst-allowance">Множитель Burst (Пиковая нагрузка)</Label>
                  <Select defaultValue="1.5">
                    <SelectTrigger id="burst-allowance">
                      <SelectValue placeholder="Выберите множитель" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1.0">1.0x (Строго)</SelectItem>
                      <SelectItem value="1.5">1.5x (Умеренно)</SelectItem>
                      <SelectItem value="2.0">2.0x (Гибко)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Маршрутизация и Доставка</CardTitle>
                <CardDescription>Настройка поведения маршрутизации.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                 <div className="space-y-2">
                  <Label htmlFor="default-sender">Sender ID по умолчанию</Label>
                  <Input id="default-sender" defaultValue="NOTICE" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dlr-expiry">Срок жизни DLR (Часы)</Label>
                  <Input id="dlr-expiry" type="number" defaultValue="48" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="route-failover">Автоматическое переключение (Failover)</Label>
                  <Select defaultValue="enabled">
                    <SelectTrigger id="route-failover">
                      <SelectValue placeholder="Выберите статус" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="enabled">Включено</SelectItem>
                      <SelectItem value="disabled">Выключено</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">Автоматически переключать на резервные маршруты при сбое.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="encoding">Кодировка по умолчанию</Label>
                   <Select defaultValue="gsm">
                    <SelectTrigger id="encoding">
                      <SelectValue placeholder="Выберите кодировку" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gsm">GSM 03.38</SelectItem>
                      <SelectItem value="ucs2">UCS-2 (Unicode)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
           </div>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Доступ и Контроль
              </CardTitle>
              <CardDescription>Политики безопасности для пользователей.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                    <Label htmlFor="min-pass-len">Мин. длина пароля</Label>
                    <Input id="min-pass-len" type="number" defaultValue="8" />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="session-timeout">Тайм-аут сессии (Минуты)</Label>
                    <Input id="session-timeout" type="number" defaultValue="60" />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="mfa-policy">Политика 2FA</Label>
                <Select defaultValue="optional">
                  <SelectTrigger id="mfa-policy">
                    <SelectValue placeholder="Выберите политику" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="optional">Опционально</SelectItem>
                    <SelectItem value="admin_only">Только Админы</SelectItem>
                    <SelectItem value="all_users">Все пользователи (Обязательно)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                  <Label htmlFor="ip-whitelist">Белый список IP (Доступ в Админку)</Label>
                  <Input id="ip-whitelist" placeholder="192.168.1.1, 10.0.0.0/24" />
                  <p className="text-xs text-muted-foreground">Список разрешенных IP/CIDR через запятую.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-4">
           <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Системные Оповещения
                </CardTitle>
                <CardDescription>Настройка уведомлений для администраторов.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                 <div className="space-y-2">
                  <Label htmlFor="alert-email">Email для оповещений</Label>
                  <Input id="alert-email" defaultValue="alerts@tenx.com" />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                        <Label htmlFor="low-bal-thresh">Порог низкого баланса</Label>
                         <div className="flex items-center gap-2">
                            <span className="text-sm font-bold">$</span>
                            <Input id="low-bal-thresh" type="number" defaultValue="10.00" />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="failure-rate">Порог ошибок (%)</Label>
                         <div className="flex items-center gap-2">
                            <Input id="failure-rate" type="number" defaultValue="5" />
                            <span className="text-sm font-bold">%</span>
                        </div>
                    </div>
                </div>
              </CardContent>
           </Card>
        </TabsContent>

        {/* System Settings */}
        <TabsContent value="system" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity className="h-5 w-5" />
                            Здоровье Системы и Логи
                        </CardTitle>
                        <CardDescription>Обслуживание и отладка.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="log-retention">Хранение логов (Дней)</Label>
                            <Input id="log-retention" type="number" defaultValue="90" />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="debug-mode">Режим отладки</Label>
                             <Select defaultValue="off">
                                <SelectTrigger id="debug-mode">
                                <SelectValue placeholder="Выберите режим" />
                                </SelectTrigger>
                                <SelectContent>
                                <SelectItem value="off">Выкл (Production)</SelectItem>
                                <SelectItem value="on">Вкл (Verbose)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                 <Card className="border-destructive/50 bg-destructive/10">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-destructive">
                            <AlertTriangle className="h-5 w-5" />
                            Опасная Зона
                        </CardTitle>
                        <CardDescription>Критические настройки.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="maintenance-mode">Режим Обслуживания</Label>
                            <Select defaultValue="inactive">
                                <SelectTrigger id="maintenance-mode" className="border-destructive/50">
                                <SelectValue placeholder="Выберите статус" />
                                </SelectTrigger>
                                <SelectContent>
                                <SelectItem value="inactive">Неактивен (Система работает)</SelectItem>
                                <SelectItem value="active">Активен (Система отключена)</SelectItem>
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-destructive">
                                Активация режима обслуживания отклонит весь входящий API трафик.
                            </p>
                        </div>
                        <Button variant="destructive" className="w-full">
                            <Lock className="mr-2 h-4 w-4" />
                            Очистить Redis Кэш
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}