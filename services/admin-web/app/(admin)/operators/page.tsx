"use client"

import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Plus, Pencil, Trash2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import type { Operator } from "@/types/api"
import { format } from "date-fns"
import { ru } from "date-fns/locale"

const operatorSchema = z.object({
  name: z.string().min(1, "Имя обязательно"),
  smpp_host: z.string().min(1, "SMPP хост обязателен"),
  smpp_port: z.coerce.number().min(1, "Укажите валидный порт").max(65535, "Порт должен быть <= 65535"),
  system_id: z.string().min(1, "System ID обязателен"),
  password: z.string().min(1, "Пароль обязателен"),
  system_type: z.string().optional(),
  status: z.enum(["active", "inactive"]),
})

type OperatorFormValues = z.infer<typeof operatorSchema>

export default function OperatorsPage() {
  const [operators, setOperators] = useState<Operator[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingOperator, setEditingOperator] = useState<Operator | null>(null)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<OperatorFormValues>({
    resolver: zodResolver(operatorSchema),
    defaultValues: {
      status: "active",
    },
  })

  const statusValue = watch("status")

  useEffect(() => {
    loadOperators()
  }, [])

  const loadOperators = async () => {
    try {
      setIsLoading(true)
      const data = await api.operators.list()
      setOperators(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки операторов")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingOperator(null)
    reset({
      name: "",
      smpp_host: "",
      smpp_port: 2775,
      system_id: "",
      password: "",
      system_type: "",
      status: "active",
    })
    setIsDialogOpen(true)
  }

  const handleEdit = (operator: Operator) => {
    setEditingOperator(operator)
    reset({
      name: operator.name,
      smpp_host: operator.smpp_host,
      smpp_port: operator.smpp_port,
      system_id: operator.system_id,
      password: "",
      system_type: operator.system_type || "",
      status: operator.status,
    })
    setIsDialogOpen(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить этого оператора?")) return

    try {
      await api.operators.delete(id)
      await loadOperators()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка удаления оператора")
    }
  }

  const onSubmit = async (data: OperatorFormValues) => {
    try {
      if (editingOperator) {
        await api.operators.update(editingOperator.id, data)
      } else {
        await api.operators.create(data)
      }
      setIsDialogOpen(false)
      await loadOperators()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка сохранения оператора")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Операторы</h1>
          <p className="text-gray-500 mt-2">
            Управление SMPP подключениями
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="w-4 h-4 mr-2" />
          Создать Оператора
        </Button>
      </div>

      {error && (
        <div className="p-4 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Список операторов</CardTitle>
          <CardDescription>SMPP операторы и их статус</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-gray-500">Загрузка операторов...</p>
          ) : operators.length === 0 ? (
            <p className="text-sm text-gray-500">Операторы не настроены</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Имя</TableHead>
                  <TableHead>SMPP Хост</TableHead>
                  <TableHead>Порт</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Здоровье</TableHead>
                  <TableHead>Создан</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {operators.map((operator) => (
                  <TableRow key={operator.id}>
                    <TableCell className="font-medium">{operator.name}</TableCell>
                    <TableCell>{operator.smpp_host}</TableCell>
                    <TableCell>{operator.smpp_port}</TableCell>
                    <TableCell>
                      <Badge variant={operator.status === "active" ? "success" : "secondary"}>
                        {operator.status === "active" ? "Активен" : "Неактивен"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          operator.health_status === "healthy"
                            ? "success"
                            : operator.health_status === "unhealthy"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {operator.health_status || "неизвестно"}
                      </Badge>
                    </TableCell>
                    <TableCell>{format(new Date(operator.created_at), "d MMM yyyy", { locale: ru })}</TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(operator)}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(operator.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingOperator ? "Редактировать Оператора" : "Создать Оператора"}
            </DialogTitle>
            <DialogDescription>
              {editingOperator
                ? "Изменить конфигурацию оператора"
                : "Добавить новое SMPP подключение"}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Имя</Label>
              <Input id="name" {...register("name")} />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="smpp_host">SMPP Хост</Label>
                <Input id="smpp_host" {...register("smpp_host")} />
                {errors.smpp_host && (
                  <p className="text-sm text-destructive">{errors.smpp_host.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="smpp_port">SMPP Порт</Label>
                <Input id="smpp_port" type="number" {...register("smpp_port")} />
                {errors.smpp_port && (
                  <p className="text-sm text-destructive">{errors.smpp_port.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="system_id">System ID</Label>
              <Input id="system_id" {...register("system_id")} />
              {errors.system_id && (
                <p className="text-sm text-destructive">{errors.system_id.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <Input id="password" type="password" {...register("password")} />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="system_type">Тип системы (Опционально)</Label>
              <Input id="system_type" {...register("system_type")} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Статус</Label>
              <Select
                value={statusValue}
                onValueChange={(value) => setValue("status", value as "active" | "inactive")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Активен</SelectItem>
                  <SelectItem value="inactive">Неактивен</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
              >
                Отмена
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Сохранение..." : editingOperator ? "Сохранить" : "Создать"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
