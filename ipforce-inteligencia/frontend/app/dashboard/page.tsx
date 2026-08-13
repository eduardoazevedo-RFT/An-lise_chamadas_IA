"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NavBar from "@/components/NavBar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Phone, PhoneOff, Clock, FileText, AlertTriangle, TrendingUp } from "lucide-react";

interface DashboardData {
  data: string;
  total_ligacoes: number;
  atendidas: number;
  nao_atendidas: number;
  duracao_total_segundos: number;
  transcritas: number;
  analisadas: number;
  alertas: number;
  oportunidades: number;
}

interface AlertaItem {
  id: number;
  record_id: string;
  data_hora: string;
  origem: string;
  destino: string;
  status: string;
  alerta_nivel: string;
  oportunidade: boolean;
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [alertas, setAlertas] = useState<AlertaItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }
    fetch("/api/dashboard/hoje", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(setData)
      .catch(() => {});
    fetch("/api/dashboard/alertas", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => setAlertas(d.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) return <div className="flex h-screen items-center justify-center"><p>Carregando...</p></div>;

  const duracaoFmt = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <div>
      <NavBar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Ligacoes</CardTitle>
              <Phone className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.total_ligacoes || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Atendidas</CardTitle>
              <Phone className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.atendidas || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Nao Atendidas</CardTitle>
              <PhoneOff className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.nao_atendidas || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Duracao Total</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{duracaoFmt(data?.duracao_total_segundos || 0)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Transcritas</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.transcritas || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Alertas</CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.alertas || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Oportunidades</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.oportunidades || 0}</div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Alertas Recentes</CardTitle>
          </CardHeader>
          <CardContent>
            {alertas.length === 0 ? (
              <p className="text-muted-foreground">Nenhum alerta recente.</p>
            ) : (
              <div className="space-y-2">
                {alertas.map((a) => (
                  <div key={a.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                    <div>
                      <p className="font-medium">{a.origem} → {a.destino}</p>
                      <p className="text-xs text-muted-foreground">{new Date(a.data_hora).toLocaleString("pt-BR")}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={a.alerta_nivel === "critico" ? "destructive" : "secondary"}>{a.alerta_nivel}</Badge>
                      {a.oportunidade && <Badge variant="outline">Oportunidade</Badge>}
                      <button
                        className="text-sm text-primary hover:underline"
                        onClick={() => router.push(`/chamadas/${a.id}`)}
                      >
                        Ver
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
