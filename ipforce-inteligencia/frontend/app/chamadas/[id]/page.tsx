"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import NavBar from "@/components/NavBar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, TrendingUp, FileText } from "lucide-react";

export default function ChamadaDetalhePage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";

  useEffect(() => {
    if (!token) { router.push("/login"); return; }
    fetch(`/api/cdr/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(setData)
      .catch(() => {});
  }, [id, router, token]);

  if (!data) return <div className="flex h-screen items-center justify-center"><p>Carregando...</p></div>;

  const { chamada, transcricao, analise } = data;

  return (
    <div>
      <NavBar />
      <main className="p-6 space-y-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Detalhes da Chamada</h1>
          <Button variant="outline" onClick={() => router.push("/cdr")}>Voltar</Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Informacoes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p><strong>Origem:</strong> {chamada.origem}</p>
              <p><strong>Destino:</strong> {chamada.destino}</p>
              <p><strong>Data/Hora:</strong> {new Date(chamada.data_hora).toLocaleString("pt-BR")}</p>
              <p><strong>Status:</strong> <Badge>{chamada.status}</Badge></p>
              <p><strong>Duracao:</strong> {chamada.duracao}s</p>
              <p><strong>Tipo:</strong> {chamada.tipo}</p>
              <p><strong>Tronco:</strong> {chamada.tronco}</p>
              {chamada.tem_gravacao && (
                <div className="pt-4">
                  <audio controls src={`/api/gravacao/${chamada.record_id}`} className="w-full" />
                </div>
              )}
            </CardContent>
          </Card>

          {analise && (
            <Card>
              <CardHeader>
                <CardTitle>Analise da IA</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-semibold text-muted-foreground">Resumo</p>
                  <p>{analise.resumo}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-muted-foreground">Motivo do Contato</p>
                  <p>{analise.motivo_contato}</p>
                </div>
                {analise.indicio_insatisfacao && (
                  <div className="flex items-center gap-2 text-destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="font-medium">Indicio de insatisfacao detectado</span>
                  </div>
                )}
                {analise.oportunidades?.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" /> Oportunidades
                    </p>
                    {analise.oportunidades.map((opp: any, i: number) => (
                      <div key={i} className="border rounded p-2 bg-muted/50">
                        <p className="font-medium">{opp.descricao}</p>
                        <p className="text-xs text-muted-foreground">Evidencia: {opp.evidencia}</p>
                      </div>
                    ))}
                  </div>
                )}
                {analise.alerta_evidencias?.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-destructive">Evidencias de Alerta</p>
                    {analise.alerta_evidencias.map((ev: any, i: number) => (
                      <div key={i} className="border border-destructive/30 rounded p-2 bg-destructive/5">
                        <p className="font-medium text-sm">{ev.motivo}</p>
                        <p className="text-xs text-muted-foreground">"{ev.trecho}"</p>
                      </div>
                    ))}
                  </div>
                )}
                {analise.sugestoes_melhoria?.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-muted-foreground">Sugestoes de Melhoria</p>
                    <ul className="list-disc list-inside text-sm">
                      {analise.sugestoes_melhoria.map((s: string, i: number) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {transcricao && (
          <Card>
            <CardHeader className="flex flex-row items-center gap-2">
              <FileText className="h-5 w-5" />
              <CardTitle>Transcricao</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {transcricao.segmentos?.map((seg: any, i: number) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <span className="text-muted-foreground w-16 shrink-0 text-right">{seg.speaker || "SPK"}</span>
                    <span className="text-muted-foreground w-20 shrink-0">[{seg.inicio?.toFixed(2)}s]</span>
                    <span>{seg.texto}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
