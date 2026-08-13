"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NavBar from "@/components/NavBar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Play, FileText, AlertTriangle, Search } from "lucide-react";

interface ChamadaItem {
  id: number;
  record_id: string;
  data_hora: string;
  origem: string;
  destino: string;
  status: string;
  duracao: number;
  tipo: string;
  tem_gravacao: boolean;
  transcrita: boolean;
  analisada: boolean;
  alerta_nivel: string;
  oportunidade: boolean;
}

export default function CDRPage() {
  const router = useRouter();
  const [chamadas, setChamadas] = useState<ChamadaItem[]>([]);
  const [filtros, setFiltros] = useState({
    data_inicio: "",
    data_fim: "",
    origem: "",
    destino: "",
    status: "",
    alerta_nivel: "",
    page: 1,
  });
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";

  async function buscar() {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams();
    if (filtros.data_inicio) params.append("data_inicio", filtros.data_inicio);
    if (filtros.data_fim) params.append("data_fim", filtros.data_fim);
    if (filtros.origem) params.append("origem", filtros.origem);
    if (filtros.destino) params.append("destino", filtros.destino);
    if (filtros.status) params.append("status", filtros.status);
    if (filtros.alerta_nivel) params.append("alerta_nivel", filtros.alerta_nivel);
    params.append("page", String(filtros.page));
    params.append("limit", "50");
    const res = await fetch(`/api/cdr/?${params.toString()}`, { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    setChamadas(data.items || []);
    setTotal(data.total || 0);
    setLoading(false);
  }

  useEffect(() => {
    if (!token) { router.push("/login"); return; }
    buscar();
  }, [filtros.page]);

  return (
    <div>
      <NavBar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">CDR — Registros de Chamadas</h1>

        <Card>
          <CardContent className="pt-6">
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="text-xs font-medium">Data Inicio</label>
                <Input type="date" value={filtros.data_inicio} onChange={e => setFiltros({...filtros, data_inicio: e.target.value})} />
              </div>
              <div>
                <label className="text-xs font-medium">Data Fim</label>
                <Input type="date" value={filtros.data_fim} onChange={e => setFiltros({...filtros, data_fim: e.target.value})} />
              </div>
              <div>
                <label className="text-xs font-medium">Origem</label>
                <Input placeholder="Ramal ou numero" value={filtros.origem} onChange={e => setFiltros({...filtros, origem: e.target.value})} />
              </div>
              <div>
                <label className="text-xs font-medium">Destino</label>
                <Input placeholder="Numero" value={filtros.destino} onChange={e => setFiltros({...filtros, destino: e.target.value})} />
              </div>
              <div>
                <label className="text-xs font-medium">Status</label>
                <Select value={filtros.status} onChange={e => setFiltros({...filtros, status: e.target.value})}>
                  <option value="">Todos</option>
                  <option value="ATENDIDA">Atendida</option>
                  <option value="NAO_ATENDIDA">Nao Atendida</option>
                  <option value="OCUPADA">Ocupada</option>
                  <option value="FALHA">Falha</option>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium">Alerta</label>
                <Select value={filtros.alerta_nivel} onChange={e => setFiltros({...filtros, alerta_nivel: e.target.value})}>
                  <option value="">Todos</option>
                  <option value="informacao">Informacao</option>
                  <option value="atencao">Atencao</option>
                  <option value="importante">Importante</option>
                  <option value="critico">Critico</option>
                </Select>
              </div>
              <div className="flex items-end">
                <Button onClick={() => { setFiltros({...filtros, page: 1}); buscar(); }} className="w-full">
                  <Search className="h-4 w-4 mr-2"/> Buscar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resultados ({total})</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data/Hora</TableHead>
                  <TableHead>Origem</TableHead>
                  <TableHead>Destino</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duracao</TableHead>
                  <TableHead>Alerta</TableHead>
                  <TableHead>Acoes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {chamadas.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>{new Date(c.data_hora).toLocaleString("pt-BR")}</TableCell>
                    <TableCell>{c.origem}</TableCell>
                    <TableCell>{c.destino}</TableCell>
                    <TableCell>
                      <Badge variant={c.status === "ATENDIDA" ? "default" : "destructive"}>{c.status}</Badge>
                    </TableCell>
                    <TableCell>{c.duracao}s</TableCell>
                    <TableCell>
                      {c.alerta_nivel !== "informacao" && (
                        <Badge variant={c.alerta_nivel === "critico" ? "destructive" : "secondary"}>{c.alerta_nivel}</Badge>
                      )}
                      {c.oportunidade && <Badge variant="outline" className="ml-1">Opp</Badge>}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {c.tem_gravacao && (
                          <Button size="sm" variant="ghost" onClick={() => router.push(`/chamadas/${c.id}`)}>
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                        {c.transcrita && (
                          <Button size="sm" variant="ghost" onClick={() => router.push(`/chamadas/${c.id}`)}>
                            <FileText className="h-4 w-4" />
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => router.push(`/chamadas/${c.id}`)}>
                          Ver
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="flex justify-between mt-4">
              <Button variant="outline" disabled={filtros.page <= 1} onClick={() => setFiltros({...filtros, page: filtros.page - 1})}>
                Anterior
              </Button>
              <span className="text-sm text-muted-foreground">Pagina {filtros.page}</span>
              <Button variant="outline" disabled={chamadas.length < 50} onClick={() => setFiltros({...filtros, page: filtros.page + 1})}>
                Proxima
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
