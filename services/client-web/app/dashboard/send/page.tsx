"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { smsApi } from "@/lib/api/sms";
import { handleApiError } from "@/lib/api/client";
import { useAuthStore } from "@/lib/stores/auth-store";
import { SMSCheckResponse, SMSSendResponse } from "@/types/api";
import { CheckCircle2, Send, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

const smsSchema = z.object({
  mobile_phone: z
    .string()
    .min(10, "Phone number must be at least 10 digits")
    .regex(/^\+?[1-9]\d{1,14}$/, "Invalid phone number format"),
  message: z.string().min(1, "Message is required").max(1530, "Message too long"),
  from: z.string().min(3, "Sender ID must be at least 3 characters").max(11, "Sender ID too long"),
});

type SMSFormData = z.infer<typeof smsSchema>;

export default function SendSMSPage() {
  const [isChecking, setIsChecking] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [checkResult, setCheckResult] = useState<SMSCheckResponse | null>(null);
  const [sendResult, setSendResult] = useState<SMSSendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const updateUser = useAuthStore((state) => state.updateUser);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
  } = useForm<SMSFormData>({
    resolver: zodResolver(smsSchema),
    defaultValues: {
      mobile_phone: "",
      message: "",
      from: "",
    },
  });

  const formValues = watch();

  const handleCheck = async () => {
    if (!formValues.mobile_phone || !formValues.message || !formValues.from) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsChecking(true);
    setError(null);
    setCheckResult(null);

    try {
      const result = await smsApi.checkMessage({
        mobile_phone: formValues.mobile_phone,
        message: formValues.message,
        from: formValues.from,
      });
      setCheckResult(result);
      toast.success("Message checked successfully");
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      toast.error(apiError.message);
    } finally {
      setIsChecking(false);
    }
  };

  const onSubmit = async (data: SMSFormData) => {
    setIsSending(true);
    setError(null);
    setSendResult(null);

    try {
      const result = await smsApi.sendSMS(data);
      setSendResult(result);
      updateUser({ balance: result.balance_after });
      toast.success("SMS sent successfully!", {
        description: `Message ID: ${result.message_id}`,
      });
      reset();
      setCheckResult(null);
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
      toast.error("Failed to send SMS", {
        description: apiError.message,
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Send SMS</h1>
        <p className="text-muted-foreground">Send SMS messages to your customers</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Message Details</CardTitle>
            <CardDescription>Enter the recipient and message content</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="mobile_phone">Mobile Phone</Label>
                <Input
                  id="mobile_phone"
                  type="tel"
                  placeholder="+1234567890"
                  {...register("mobile_phone")}
                  disabled={isSending}
                />
                {errors.mobile_phone && (
                  <p className="text-sm text-destructive">{errors.mobile_phone.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="from">Sender ID</Label>
                <Input
                  id="from"
                  type="text"
                  placeholder="YourBrand"
                  {...register("from")}
                  disabled={isSending}
                />
                {errors.from && <p className="text-sm text-destructive">{errors.from.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message</Label>
                <Textarea
                  id="message"
                  placeholder="Enter your message here..."
                  rows={6}
                  {...register("message")}
                  disabled={isSending}
                  className="resize-none"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>
                    {errors.message ? (
                      <span className="text-destructive">{errors.message.message}</span>
                    ) : (
                      <span>{formValues.message?.length || 0} / 1530 characters</span>
                    )}
                  </span>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </div>
              )}

              {sendResult && (
                <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
                  <CheckCircle2 className="h-4 w-4" />
                  <div>
                    <p className="font-medium">Message sent successfully!</p>
                    <p className="text-xs">
                      Message ID: {sendResult.message_id} | Status: {sendResult.status}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCheck}
                  disabled={isChecking || isSending}
                >
                  {isChecking ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Checking...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Check Message
                    </>
                  )}
                </Button>

                <Button type="submit" disabled={isSending}>
                  {isSending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Send SMS
                    </>
                  )}
                </Button>
              </div>

              {checkResult && (
                <div className="rounded-md bg-muted p-3">
                  <div className="flex items-center gap-3">
                    <Badge>Preview</Badge>
                    <span className="text-sm text-muted-foreground">
                      Parts: {checkResult.message_parts} • Encoding: {checkResult.encoding} •
                      Estimated price: ${checkResult.price_estimate.toFixed(4)}
                    </span>
                  </div>
                </div>
              )}
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tips for better deliverability</CardTitle>
            <CardDescription>Improve your SMS performance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <div>
              <p className="font-medium text-foreground">Sender IDs</p>
              <p>Use a recognizable sender ID and keep it under 11 characters.</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Message content</p>
              <p>Avoid all caps, excessive links, and spammy keywords.</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Formatting</p>
              <p>Include opt-out instructions for compliance where required.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
