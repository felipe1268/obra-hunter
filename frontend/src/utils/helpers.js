import { Globe, FileText, Target, Building2 } from "lucide-react";

export const fmt = (v) => v ? `R$ ${(v / 1e6).toFixed(1)}M` : "—";
export const fmtN = (n) => n?.toLocaleString("pt-BR") || "0";

export const TIPO_STYLE = {
  residencial: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  comercial: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  industrial: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  infraestrutura: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  institucional: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  loteamento: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
};

export const STATUS_BG = {
  novo: "bg-slate-500", enriquecido: "bg-blue-500",
  contato_encontrado: "bg-indigo-500", em_prospeccao: "bg-amber-500",
  convertido: "bg-emerald-500", descartado: "bg-red-500/60",
};

export const STATUS_LABEL = {
  novo: "Novo", enriquecido: "Enriquecido",
  contato_encontrado: "Contato", em_prospeccao: "Prospectando",
  convertido: "Convertido", descartado: "Descartado",
};

export const FONTE_ICON = {
  google_maps: Globe, diario_oficial: FileText,
  licitacao: Target, construtora: Building2,
};

export const ROLE_LABEL = {
  admin: "Administrador", gerente: "Gerente",
  vendedor: "Vendedor", viewer: "Visualizador",
};

export const ROLE_STYLE = {
  admin: "text-red-400 bg-red-500/10",
  gerente: "text-amber-400 bg-amber-500/10",
  vendedor: "text-cyan-400 bg-cyan-500/10",
  viewer: "text-slate-400 bg-slate-500/10",
};

export const PRIOR_STYLE = {
  urgente: "border-l-red-500 bg-red-500/5",
  alta: "border-l-amber-500 bg-amber-500/5",
  media: "border-l-blue-500 bg-blue-500/5",
  baixa: "border-l-slate-600 bg-slate-500/5",
};
