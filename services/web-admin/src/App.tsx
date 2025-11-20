import { useMemo, useState } from "react";
import axios, { AxiosError } from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpenCheck,
  Copy,
  Download,
  Info,
  ShieldCheck,
  ShieldX,
  Stars,
  Users,
  Wallet,
  Workflow,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

import type { AuthProfile, Balance, Template } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/v1").replace(/\/$/, "");
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || "";
const DOC_URL = "/docs/otp-gateway.postman_collection.json";

const axiosClient = axios.create({ baseURL: API_BASE });

const clientTabs = [
  { id: "send", label: "Отправить СМС" },
  { id: "contacts", label: "Контакты" },
  { id: "groups", label: "Группы" },
  { id: "reports", label: "Детализация" },
  { id: "texts", label: "Мои тексты" },
  { id: "prices", label: "Цены" },
  { id: "gateway", label: "СМС шлюз" },
  { id: "nick", label: "Заявка на ник" },
  { id: "integrations", label: "Каталог интеграций" },
];

const instructionSet = {
  portal: [
    "В разделе «Контакты» скачайте XLSX-шаблон и заполните его реальными клиентами (до 10 000 номеров).",
    "Загрузите файл и разделите аудиторию по группам (например, «OTP» или «Маркетинг»).",
    "Во вкладке «Отправить СМС» выберите группу, шаблон и отправьте кампанию сразу или по расписанию.",
  ],
  gateway: [
    "Сгенерируйте X-API-Key и whitelisted IP в биллинге. Эта пара нужна для всех интеграций.",
    "Создайте текстовые шаблоны и дождитесь одобрения модератора (проверка занимает 1–2 часа).",
    "Используйте POST /otp/send с параметрами template_id + metadata. Пример запроса ниже или в Postman.",
  ],
};

const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "destructive" }> = {
  pending: { label: "На модерации", variant: "secondary" },
  approved: { label: "Одобрен", variant: "default" },
  rejected: { label: "Отклонён", variant: "destructive" },
};

const sampleContacts = [
  { id: 1, name: "Саидмирхожа", phone: "+998958603171", group: "OTP Premium", status: "Активный" },
  { id: 2, name: "Сардорбек Фозилов", phone: "+998977042000", group: "OTP Premium", status: "Активный" },
  { id: 3, name: "Хожа", phone: "+998994400706", group: "Retail Onboarding", status: "Активный" },
  { id: 4, name: "Зулайхо Абдусатторова", phone: "+998991103443", group: "Retail Onboarding", status: "Активный" },
  { id: 5, name: "Мухаммадризо Абдусатторов", phone: "+998977042000", group: "Колл-центр", status: "Активный" },
];

const priceMatrix = [
  { code: "Beeline GSM (+998 90)", service: "115 сум", promo: "300 сум" },
  { code: "Beeline GSM (+998 91)", service: "115 сум", promo: "300 сум" },
  { code: "Mobiuz GSM (+998 97)", service: "95 сум", promo: "175 сум" },
  { code: "Ucell GSM (+998 93)", service: "160 сум", promo: "340 сум" },
  { code: "Humans", service: "95 сум", promo: "95 сум" },
  { code: "Uzmobile GSM (+998 99)", service: "95 сум", promo: "175 сум" },
  { code: "Perfectum", service: "95 сум", promo: "95 сум" },
];

const integrationKits = [
  {
    name: "k6 нагрузочное тестирование",
    description: "Готовый скрипт для проверки RPS и SLA OTP трафика.",
    status: "Готово",
  },
  {
    name: "Grafana + Prometheus",
    description: "Дэшборды по попыткам, доставкам, отложенным сообщениям.",
    status: "Готово",
  },
  {
    name: "Webhook Router",
    description: "Трансформация DLR payload в формат внутренних сервисов.",
    status: "В разработке",
  },
];

type TemplateFormState = {
  name: string;
  channel: string;
  category: string;
  content: string;
  variables: string;
};

type NickFormState = {
  company: string;
  brand: string;
  comment: string;
};

const formatCurrency = (value?: string, currency?: string) => {
  if (!value) {
    return "—";
  }
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return `${value} ${currency || ""}`.trim();
  }
  try {
    return new Intl.NumberFormat("ru-RU", {
      style: "currency",
      currency: currency || "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency || ""}`.trim();
  }
};

function TemplateStatusBadge({ status }: { status: string }) {
  const meta = statusMap[status] ?? statusMap.pending;
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}

function App() {
  const queryClient = useQueryClient();
  const [activeRole, setActiveRole] = useState<"client" | "admin">("client");
  const [clientTab, setClientTab] = useState(clientTabs[0].id);
  const [instructionMode, setInstructionMode] = useState<"portal" | "gateway">("portal");
  const [apiKey, setApiKey] = useState("");
  const [adminToken, setAdminToken] = useState(ADMIN_TOKEN);
  const [templateForm, setTemplateForm] = useState<TemplateFormState>({
    name: "",
    channel: "sms",
    category: "",
    content: "Ваш OTP: {{code}}. Никому не сообщайте.",
    variables: "code",
  });
  const [nickForm, setNickForm] = useState<NickFormState>({ company: "", brand: "", comment: "" });
  const [nickSubmitted, setNickSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [rejectModal, setRejectModal] = useState<{ id: string; name: string } | null>(null);
  const [rejectComment, setRejectComment] = useState("");

  const hasApiKey = Boolean(apiKey);
  const hasAdminToken = Boolean(adminToken);

  const templateQuery = useQuery({
    queryKey: ["templates", apiKey],
    enabled: hasApiKey,
    queryFn: async () => {
      const res = await axiosClient.get<Template[]>("/templates", {
        headers: { "X-API-Key": apiKey },
      });
      return res.data;
    },
  });

  const balanceQuery = useQuery({
    queryKey: ["balance", apiKey],
    enabled: hasApiKey,
    queryFn: async () => {
      const res = await axiosClient.get<Balance>("/balance", {
        headers: { "X-API-Key": apiKey },
      });
      return res.data;
    },
    staleTime: 30_000,
  });

  const profileQuery = useQuery({
    queryKey: ["profile", apiKey],
    enabled: hasApiKey,
    queryFn: async () => {
      const res = await axiosClient.get<AuthProfile>("/profile", {
        headers: { "X-API-Key": apiKey },
      });
      return res.data;
    },
    staleTime: 60_000,
  });

  const pendingTemplatesQuery = useQuery({
    queryKey: ["pending-templates", adminToken],
    enabled: hasAdminToken,
    queryFn: async () => {
      const res = await axiosClient.get<Template[]>("/admin/templates", {
        headers: { "X-Admin-Token": adminToken },
      });
      return res.data;
    },
  });

  const handleError = (err: unknown) => {
    console.error(err);
    if (err instanceof AxiosError) {
      setError(err.response?.data?.detail || err.message);
    } else if (err instanceof Error) {
      setError(err.message);
    } else {
      setError("Неизвестная ошибка");
    }
  };

  const createTemplateMutation = useMutation({
    mutationFn: async () => {
      setError(null);
      setNotice(null);
      const payload = {
        name: templateForm.name,
        channel: templateForm.channel,
        category: templateForm.category || null,
        content: templateForm.content,
        variables: templateForm.variables
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
      };
      const res = await axiosClient.post("/templates", payload, {
        headers: { "X-API-Key": apiKey },
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates", apiKey] });
      setTemplateForm((prev) => ({ ...prev, name: "", category: "" }));
      setNotice("Шаблон отправлен на модерацию. Обычно проверка занимает до 2 часов.");
    },
    onError: handleError,
  });

  const decisionMutation = useMutation({
    mutationFn: async ({
      templateId,
      status,
      comment,
    }: {
      templateId: string;
      status: "approved" | "rejected";
      comment?: string;
    }) => {
      setError(null);
      setNotice(null);
      const res = await axiosClient.post(
        `/admin/templates/${templateId}/decision`,
        { status, comment },
        { headers: { "X-Admin-Token": adminToken } },
      );
      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["pending-templates", adminToken] });
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      setRejectModal(null);
      setRejectComment("");
      setNotice(
        variables.status === "approved"
          ? "Шаблон одобрен и доступен клиенту."
          : "Шаблон отклонён. Клиент увидит комментарий.",
      );
    },
    onError: handleError,
  });

  const nickSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNickSubmitted(true);
    setNotice("Заявка на ник отправлена. Ответ придёт на e-mail администратора.");
  };

  const clientView = (
    <Tabs value={clientTab} onValueChange={(value) => setClientTab(value)} className="space-y-4">
      <TabsList className="flex flex-wrap gap-2 overflow-x-auto">
        {clientTabs.map((tab) => (
          <TabsTrigger key={tab.id} value={tab.id}>
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>

      <TabsContent value="send" className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="h-5 w-5 text-primary" />
                Баланс и лимиты
              </CardTitle>
              <CardDescription>Данные реального времени из биллинга.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {hasApiKey ? (
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-xs uppercase text-muted-foreground">Баланс</p>
                    <p className="text-2xl font-semibold">
                      {formatCurrency(balanceQuery.data?.balance, balanceQuery.data?.currency)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase text-muted-foreground">Кредитный лимит</p>
                    <p className="text-2xl font-semibold">
                      {formatCurrency(balanceQuery.data?.credit_limit, balanceQuery.data?.currency)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase text-muted-foreground">RPS</p>
                    <p className="text-2xl font-semibold">
                      {profileQuery.data?.rate_limit_rps ?? "—"}
                      {profileQuery.data?.rate_limit_rps ? " /сек" : ""}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Укажите X-API-Key, чтобы увидеть баланс и лимиты аккаунта.
                </p>
              )}
              <div className="flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  onClick={() => balanceQuery.refetch()}
                  disabled={!hasApiKey || balanceQuery.isFetching}
                >
                  Обновить
                </Button>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="secondary">Инструкция по пополнению</Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Как пополнить баланс</DialogTitle>
                      <DialogDescription>
                        Средства зачисляются в течение 5–15 минут после оплаты.
                      </DialogDescription>
                    </DialogHeader>
                    <ol className="list-decimal space-y-3 pl-4 text-sm text-muted-foreground">
                      <li>Создайте счёт в ERP или запросите инвойс у менеджера поддержки.</li>
                      <li>
                        Переведите сумму по реквизитам ТОО «Jasmin Aggregator». Назначение платежа:
                        <i> Пополнение SMS-гейтвея</i>.
                      </li>
                      <li>Отправьте платежку на finance@otp-gateway.io и ожидайте подтверждения.</li>
                      <li>После зачисления баланс и лимиты обновятся автоматически.</li>
                    </ol>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpenCheck className="h-5 w-5 text-primary" />
                Конфигурация API
              </CardTitle>
              <CardDescription>Данные для подключения по HTTP.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <p className="text-xs uppercase text-muted-foreground">Endpoint</p>
                <div className="flex items-center justify-between rounded-md border bg-muted/40 px-3 py-2 text-sm font-mono">
                  <span>{API_BASE}</span>
                  <Button variant="ghost" size="icon" onClick={() => navigator.clipboard.writeText(API_BASE)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs uppercase text-muted-foreground">X-API-Key</p>
                <Input
                  type="password"
                  placeholder="sk_live_XXXX"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value.trim())}
                />
              </div>
              {profileQuery.data && (
                <div className="space-y-1 text-sm">
                  <p className="text-xs uppercase text-muted-foreground">ID аккаунта</p>
                  <code className="rounded bg-muted px-2 py-1 text-xs">{profileQuery.data.account_id}</code>
                </div>
              )}
              <Button asChild variant="outline" className="w-full gap-2">
                <a href={DOC_URL} download>
                  <Download className="h-4 w-4" />
                  Скачать Postman
                </a>
              </Button>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Инструкция по отправке</CardTitle>
            <CardDescription>Шаги для self-service и прямого API.</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs
              value={instructionMode}
              onValueChange={(value) => setInstructionMode(value as "portal" | "gateway")}
              className="space-y-4"
            >
              <TabsList>
                <TabsTrigger value="portal">Через кабинет</TabsTrigger>
                <TabsTrigger value="gateway">Через СМС шлюз</TabsTrigger>
              </TabsList>
              <TabsContent value="portal">
                <ol className="list-decimal space-y-3 pl-4 text-sm text-muted-foreground">
                  {instructionSet.portal.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
              </TabsContent>
              <TabsContent value="gateway">
                <ol className="list-decimal space-y-3 pl-4 text-sm text-muted-foreground">
                  {instructionSet.gateway.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="contacts">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Контакты
            </CardTitle>
            <CardDescription>Загрузите XLSX-шаблон или добавляйте клиентов вручную.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary">+ Добавить по одному</Button>
              <Button variant="outline">Загрузить контакты (.xlsx)</Button>
              <Button variant="outline">Скачать шаблон</Button>
              <Button variant="ghost" className="text-destructive">
                Удалить выбранные
              </Button>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ф.И.О</TableHead>
                  <TableHead>Телефон</TableHead>
                  <TableHead>Группа</TableHead>
                  <TableHead>Статус</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sampleContacts.map((contact) => (
                  <TableRow key={contact.id}>
                    <TableCell>{contact.name}</TableCell>
                    <TableCell className="font-mono">{contact.phone}</TableCell>
                    <TableCell>{contact.group}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{contact.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="groups">
        <Card>
          <CardHeader>
            <CardTitle>Группы</CardTitle>
            <CardDescription>Сегментация клиентов по продуктам и каналам.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            {["OTP Premium", "Retail Onboarding", "Колл-центр"].map((group) => {
              const count = sampleContacts.filter((c) => c.group === group).length;
              return (
                <div key={group} className="rounded-xl border p-4">
                  <p className="text-sm text-muted-foreground">Группа</p>
                  <p className="text-lg font-semibold">{group}</p>
                  <p className="text-sm text-muted-foreground">{count} контактов</p>
                  <Button variant="link" className="px-0">
                    Управлять
                  </Button>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="reports">
        <Card>
          <CardHeader>
            <CardTitle>Детализация отправок</CardTitle>
            <CardDescription>Статусы операторов и причины недоставки.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border p-4">
                <p className="font-medium">Основные статусы</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-muted-foreground">
                  <li>В ожидании — сообщение готовится к передаче оператору.</li>
                  <li>Передано — оператор принял сообщение, ожидается DLR.</li>
                  <li>Доставлено — оператор подтвердил доставку.</li>
                  <li>Не доставлено — номер вне сети, заблокирован или в чёрном списке.</li>
                </ul>
              </div>
              <div className="rounded-lg border p-4">
                <p className="font-medium">Экспорт отчётов</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Доступны выгрузки по датам, операторам и статусам в CSV/JSON. Автоотправка по e-mail или в
                  сторонние BI-системы.
                </p>
                <Button variant="outline" className="mt-4">
                  Скачать пример CSV
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="texts" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Новый шаблон</CardTitle>
            <CardDescription>Заполните текст и переменные — остальное сделает модератор.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!hasApiKey && (
              <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
                Укажите X-API-Key, чтобы отправлять шаблоны от имени своего аккаунта.
              </div>
            )}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="tpl-name">Название</Label>
                <Input
                  id="tpl-name"
                  value={templateForm.name}
                  placeholder="OTP авторизация"
                  onChange={(e) => setTemplateForm((prev) => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Канал</Label>
                <Select
                  value={templateForm.channel}
                  onValueChange={(value) => setTemplateForm((prev) => ({ ...prev, channel: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="sms" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sms">SMS</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="tpl-category">Категория</Label>
                <Input
                  id="tpl-category"
                  value={templateForm.category}
                  placeholder="Безопасность"
                  onChange={(e) => setTemplateForm((prev) => ({ ...prev, category: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tpl-vars">Переменные (через запятую)</Label>
                <Input
                  id="tpl-vars"
                  value={templateForm.variables}
                  placeholder="code, clientName"
                  onChange={(e) => setTemplateForm((prev) => ({ ...prev, variables: e.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tpl-content">Текст</Label>
              <Textarea
                id="tpl-content"
                rows={5}
                value={templateForm.content}
                onChange={(e) => setTemplateForm((prev) => ({ ...prev, content: e.target.value }))}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                onClick={() => createTemplateMutation.mutate()}
                disabled={!hasApiKey || createTemplateMutation.isPending}
              >
                Отправить на модерацию
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Мои тексты</CardTitle>
            <CardDescription>Статусы, комментарии и дата последнего изменения.</CardDescription>
          </CardHeader>
          <CardContent>
            {templateQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Загрузка...</p>
            ) : templateQuery.data && templateQuery.data.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Название</TableHead>
                    <TableHead>Переменные</TableHead>
                    <TableHead>Статус</TableHead>
                    <TableHead>Комментарий</TableHead>
                    <TableHead className="text-right">Обновлено</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {templateQuery.data.map((tpl) => (
                    <TableRow key={tpl.id}>
                      <TableCell>
                        <p className="font-medium">{tpl.name}</p>
                        <p className="text-xs text-muted-foreground">{tpl.content}</p>
                      </TableCell>
                      <TableCell>{tpl.variables?.join(", ") || "—"}</TableCell>
                      <TableCell>
                        <TemplateStatusBadge status={tpl.status} />
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {tpl.admin_comment || "Без комментария"}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {new Date(tpl.updated_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground">Шаблонов пока нет — создайте первый выше.</p>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="prices">
        <Card>
          <CardHeader>
            <CardTitle>Тарифы по операторам (Узбекистан)</CardTitle>
            <CardDescription>Сервисные и рекламные сообщения тарифицируются отдельно.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Код / оператор</TableHead>
                  <TableHead>Сервисный</TableHead>
                  <TableHead>Рекламный</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {priceMatrix.map((row) => (
                  <TableRow key={row.code}>
                    <TableCell className="font-medium">{row.code}</TableCell>
                    <TableCell>{row.service}</TableCell>
                    <TableCell>{row.promo}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="gateway">
        <Card>
          <CardHeader>
            <CardTitle>СМС шлюз и интеграции</CardTitle>
            <CardDescription>HTTP API, DLR и пример запроса.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border bg-muted/40 p-4 text-sm text-muted-foreground">
              <p className="font-medium text-foreground">Пример запроса</p>
              <pre className="mt-2 overflow-x-auto text-xs">
{`curl -X POST ${API_BASE}/otp/send \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ${apiKey || "sk_live_XXXX"}" \\
  -d '{
    "to": "+998991112233",
    "template_id": "UUID",
    "metadata": { "code": "654123" },
    "sender": "ANORBANK",
    "dlr_callback_url": "https://your-app.example.com/dlr"
  }'`}
              </pre>
            </div>
            <div className="rounded-lg border p-4">
              <p className="font-medium">Delivery Report</p>
              <p className="text-sm text-muted-foreground">
                Укажите dlr_callback_url — мы пришлём JSON с полем status (DELIVERED, REJECTED, UNKNOWN) и
                оригинальными metadata.
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="nick">
        <Card>
          <CardHeader>
            <CardTitle>Заявка на альфа-имя (ник)</CardTitle>
            <CardDescription>Обязательная процедура у местных операторов.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={nickSubmit}>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Компания</Label>
                  <Input
                    required
                    value={nickForm.company}
                    onChange={(e) => setNickForm((prev) => ({ ...prev, company: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Желаемый ник (отправитель)</Label>
                  <Input
                    required
                    value={nickForm.brand}
                    maxLength={11}
                    onChange={(e) => setNickForm((prev) => ({ ...prev, brand: e.target.value.toUpperCase() }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Комментарий</Label>
                <Textarea
                  rows={3}
                  value={nickForm.comment}
                  onChange={(e) => setNickForm((prev) => ({ ...prev, comment: e.target.value }))}
                />
              </div>
              <div className="flex items-center gap-2">
                <input id="confirm-nick" type="checkbox" required className="h-4 w-4" />
                <Label htmlFor="confirm-nick" className="text-sm text-muted-foreground">
                  Подтверждаю, что текст соответствует правилам операторов.
                </Label>
              </div>
              <Button type="submit" disabled={nickSubmitted}>
                {nickSubmitted ? "Отправлено" : "Отправить заявку"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="integrations">
        <Card>
          <CardHeader>
            <CardTitle>Каталог интеграций</CardTitle>
            <CardDescription>Расширения и готовые сценарии.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            {integrationKits.map((kit) => (
              <div key={kit.name} className="rounded-xl border p-4">
                <p className="font-medium">{kit.name}</p>
                <p className="text-sm text-muted-foreground">{kit.description}</p>
                <Badge className="mt-3" variant={kit.status === "Готово" ? "default" : "secondary"}>
                  {kit.status}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );

  const adminView = (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Сервисный токен</CardTitle>
          <CardDescription>Админ-доступ для быстрой модерации шаблонов.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Label htmlFor="admin-token">X-Admin-Token</Label>
          <Input
            id="admin-token"
            placeholder="admin-secret"
            value={adminToken}
            onChange={(e) => setAdminToken(e.target.value.trim())}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Workflow className="h-5 w-5 text-primary" />
            Очередь модерации
          </CardTitle>
          <CardDescription>Одобряйте или отклоняйте тексты в пару кликов.</CardDescription>
        </CardHeader>
        <CardContent>
          {!hasAdminToken ? (
            <p className="text-sm text-muted-foreground">Введите токен, чтобы увидеть ожидающие шаблоны.</p>
          ) : pendingTemplatesQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Загрузка...</p>
          ) : pendingTemplatesQuery.data && pendingTemplatesQuery.data.length > 0 ? (
            <div className="space-y-4">
              {pendingTemplatesQuery.data.map((tpl) => (
                <div key={tpl.id} className="rounded-xl border p-4 shadow-sm">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="text-xs uppercase text-muted-foreground">{tpl.channel}</p>
                      <h3 className="text-lg font-semibold">{tpl.name}</h3>
                      <p className="text-sm text-muted-foreground">{tpl.account_id}</p>
                    </div>
                    <TemplateStatusBadge status={tpl.status} />
                  </div>
                  <p className="mt-3 rounded-md bg-muted/50 p-3 font-mono text-sm leading-relaxed">{tpl.content}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {tpl.variables?.map((v) => (
                      <Badge key={v} variant="outline">
                        {v}
                      </Badge>
                    )) || <span>Без переменных</span>}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      className="border-green-600 text-green-600 hover:bg-green-50"
                      disabled={decisionMutation.isPending}
                      onClick={() => decisionMutation.mutate({ templateId: tpl.id, status: "approved" })}
                    >
                      <ShieldCheck className="mr-2 h-4 w-4" />
                      Одобрить
                    </Button>
                    <Button
                      variant="destructive"
                      disabled={decisionMutation.isPending}
                      onClick={() => {
                        setRejectModal({ id: tpl.id, name: tpl.name });
                        setRejectComment("");
                      }}
                    >
                      <ShieldX className="mr-2 h-4 w-4" />
                      Отклонить
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Все тексты обработаны. Ждём новых заявок.</p>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={Boolean(rejectModal)}
        onOpenChange={(open) => {
          if (!open) {
            setRejectModal(null);
            setRejectComment("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Отклонить шаблон</DialogTitle>
            <DialogDescription>
              Укажите причину, она появится у клиента в карточке шаблона.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Комментарий</Label>
            <Textarea
              rows={4}
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
              placeholder="Например: добавьте название сервиса или замените {{pin}} на {{code}}"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setRejectModal(null)}>
              Отмена
            </Button>
            <Button
              variant="destructive"
              disabled={!rejectModal}
              onClick={() =>
                rejectModal &&
                decisionMutation.mutate({
                  templateId: rejectModal.id,
                  status: "rejected",
                  comment: rejectComment || undefined,
                })
              }
            >
              Отклонить
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm uppercase tracking-widest text-muted-foreground">
              <Stars className="h-4 w-4 text-primary" />
              Jasmin OTP Gateway
            </div>
            <h1 className="text-3xl font-semibold tracking-tight">Контрольный центр</h1>
            <p className="text-muted-foreground">
              Баланс, шаблоны, интеграции и модерация — в одном интерфейсе.
            </p>
          </div>
          <Tabs value={activeRole} onValueChange={(value) => setActiveRole(value as "client" | "admin")}>
            <TabsList>
              <TabsTrigger value="client">Клиент</TabsTrigger>
              <TabsTrigger value="admin">Админ</TabsTrigger>
            </TabsList>
          </Tabs>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Подключение окружения</CardTitle>
            <CardDescription>Укажите ключи, которые выдали в биллинге.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>API Gateway URL</Label>
              <div className="flex items-center gap-2">
                <Input value={API_BASE} readOnly className="font-mono" />
                <Button size="icon" variant="outline" onClick={() => navigator.clipboard.writeText(API_BASE)}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label>X-API-Key клиента</Label>
              <Input
                type="password"
                placeholder="sk_live_XXXX"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value.trim())}
              />
            </div>
            <div className="space-y-2">
              <Label>Admin token (для модерации)</Label>
              <Input
                type="password"
                placeholder="admin-secret"
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value.trim())}
              />
            </div>
            <div className="space-y-2">
              <Label>Документация</Label>
              <Button asChild variant="outline" className="gap-2">
                <a href={DOC_URL} download>
                  <Download className="h-4 w-4" />
                  Скачать Postman коллекцию
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="rounded-md border border-destructive bg-destructive/10 p-4 text-destructive">
            <strong>Ошибка:</strong> {error}
          </div>
        )}

        {notice && (
          <div className="flex items-center justify-between rounded-md border border-emerald-300 bg-emerald-50 p-4 text-sm text-emerald-900">
            <span>{notice}</span>
            <Button variant="ghost" size="icon" onClick={() => setNotice(null)}>
              ✕
            </Button>
          </div>
        )}

        {activeRole === "client" ? clientView : adminView}
      </div>
    </div>
  );
}

export default App;

