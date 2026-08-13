"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErro("");
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
      if (!res.ok) throw new Error("Credenciais invalidas");
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setErro(err.message || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-muted/40">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>IPForce Inteligencia</CardTitle>
          <p className="text-sm text-muted-foreground">Entre com suas credenciais</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="text-sm font-medium">Senha</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {erro && <p className="text-sm text-destructive">{erro}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
