import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">Qalb SMS</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Create your account
          </p>
        </div>
        <RegisterForm />
      </div>
    </div>
  );
}
