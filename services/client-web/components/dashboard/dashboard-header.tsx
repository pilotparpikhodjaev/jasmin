"use client";

import { useAuthStore } from "@/lib/stores/auth-store";
import { Button } from "@/components/ui/button";
import { LogOut, Wallet, MessageSquare } from "lucide-react";
import { useRouter } from "next/navigation";

export function DashboardHeader() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold">
          Welcome, {user?.name || user?.username}
        </h1>
      </div>
      <div className="flex items-center gap-4">
        {user?.balance !== undefined && (
          <div className="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-1.5">
            <Wallet className="h-4 w-4 text-slate-600" />
            <span className="text-sm font-medium">
              ${user.balance.toFixed(2)}
            </span>
          </div>
        )}
        {user?.sms_count !== undefined && (
          <div className="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-1.5">
            <MessageSquare className="h-4 w-4 text-slate-600" />
            <span className="text-sm font-medium">{user.sms_count} SMS</span>
          </div>
        )}
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </Button>
      </div>
    </header>
  );
}
