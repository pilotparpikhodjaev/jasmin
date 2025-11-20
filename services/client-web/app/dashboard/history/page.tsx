"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { smsApi } from "@/lib/api/sms";
import { handleApiError } from "@/lib/api/client";
import { SMSMessage } from "@/types/api";
import { Loader2, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";

const statusColors: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DELIVRD: "default",
  PENDING: "secondary",
  UNDELIV: "destructive",
  EXPIRED: "outline",
  REJECTED: "destructive",
  FAILED: "destructive",
};

export default function MessageHistoryPage() {
  const [messages, setMessages] = useState<SMSMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<SMSMessage | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    status: "",
    start_date: "",
    end_date: "",
  });

  const fetchMessages = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await smsApi.getUserMessages({
        page,
        page_size: 50,
        status: filters.status || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
      });
      setMessages(result.data);
      setTotalPages(result.total_pages);
      setTotal(result.total);
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handleFilter = () => {
    setPage(1);
    fetchMessages();
  };

  const handleViewDetails = async (messageId: string) => {
    try {
      const message = await smsApi.getMessageById(messageId);
      setSelectedMessage(message);
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError.message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Message History</h1>
        <p className="text-muted-foreground">View and search your sent messages</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter messages by status and date range</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <option value="">All Status</option>
                <option value="DELIVRD">Delivered</option>
                <option value="PENDING">Pending</option>
                <option value="UNDELIV">Undelivered</option>
                <option value="EXPIRED">Expired</option>
                <option value="REJECTED">Rejected</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="start_date">Start Date</Label>
              <Input
                id="start_date"
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end_date">End Date</Label>
              <Input
                id="end_date"
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>

            <div className="flex items-end">
              <Button onClick={handleFilter} className="w-full">
                <Search className="mr-2 h-4 w-4" />
                Apply Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Messages</CardTitle>
              <CardDescription>
                Showing {messages.length} of {total} messages
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : messages.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">No messages found</div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-left text-sm font-medium text-muted-foreground">
                      <th className="pb-3">Message ID</th>
                      <th className="pb-3">Phone</th>
                      <th className="pb-3">Message</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3">Date</th>
                      <th className="pb-3 text-right">Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {messages.map((message) => (
                      <tr
                        key={message.message_id}
                        className="cursor-pointer border-b transition-colors hover:bg-muted/50"
                        onClick={() => handleViewDetails(message.message_id)}
                      >
                        <td className="py-3">
                          <span className="font-mono text-xs">{message.message_id.slice(0, 8)}</span>
                        </td>
                        <td className="py-3">{message.mobile_phone}</td>
                        <td className="py-3">
                          <span className="line-clamp-1 max-w-xs">{message.message}</span>
                        </td>
                        <td className="py-3">
                          <Badge variant={statusColors[message.status] || "outline"}>
                            {message.status}
                          </Badge>
                        </td>
                        <td className="py-3 text-sm text-muted-foreground">
                          {format(new Date(message.created_at), "MMM dd, yyyy HH:mm")}
                        </td>
                        <td className="py-3 text-right font-mono text-sm">
                          ${message.price.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Previous
                </Button>
                <div className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {selectedMessage && (
        <Card>
          <CardHeader>
            <CardTitle>Message Details</CardTitle>
            <CardDescription>ID: {selectedMessage.message_id}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-muted-foreground">Phone</p>
                <p className="font-medium">{selectedMessage.mobile_phone}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant={statusColors[selectedMessage.status] || "outline"}>
                  {selectedMessage.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sent At</p>
                <p className="font-medium">
                  {format(new Date(selectedMessage.created_at), "MMM dd, yyyy HH:mm")}
                </p>
              </div>
              {selectedMessage.delivered_at && (
                <div>
                  <p className="text-sm text-muted-foreground">Delivered At</p>
                  <p className="font-medium">
                    {format(new Date(selectedMessage.delivered_at), "MMM dd, yyyy HH:mm")}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">Price</p>
                <p className="font-medium">${selectedMessage.price.toFixed(4)}</p>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Message</p>
              <p className="font-medium">{selectedMessage.message}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
