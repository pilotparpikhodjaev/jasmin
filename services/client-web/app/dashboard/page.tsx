import { DashboardStats } from "@/components/dashboard/dashboard-stats";
import { RecentMessages } from "@/components/dashboard/recent-messages";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to your SMS platform overview
        </p>
      </div>
      <DashboardStats />
      <RecentMessages />
    </div>
  );
}
