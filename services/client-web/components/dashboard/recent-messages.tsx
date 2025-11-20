"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { format } from "date-fns";

const mockMessages = [
  { id: "1", from: "+1234567890", to: "+0987654321", status: "delivered", createdAt: new Date() },
  { id: "2", from: "+1234567890", to: "+0987654322", status: "pending", createdAt: new Date() },
  { id: "3", from: "+1234567890", to: "+0987654323", status: "failed", createdAt: new Date() },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case "delivered":
      return "text-green-600";
    case "pending":
      return "text-yellow-600";
    case "failed":
      return "text-red-600";
    default:
      return "text-gray-600";
  }
};

export function RecentMessages() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Messages</CardTitle>
        <CardDescription>Latest SMS activity from your account</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockMessages.map((message) => (
            <div
              key={message.id}
              className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
            >
              <div className="space-y-1">
                <p className="text-sm font-medium">
                  {message.from} → {message.to}
                </p>
                <p className="text-xs text-muted-foreground">
                  {format(message.createdAt, "PPpp")}
                </p>
              </div>
              <span
                className={`text-sm font-medium capitalize ${getStatusColor(message.status)}`}
              >
                {message.status}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
