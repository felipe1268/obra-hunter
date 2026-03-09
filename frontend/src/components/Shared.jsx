import { MapPin, ArrowUpRight, Building2 } from "lucide-react";
import { fmt, fmtN, TIPO_STYLE, STATUS_BG, STATUS_LABEL, FONTE_ICON } from "../utils/helpers";

export function ScoreBadge({ score, size = "md" }) {
  const g = score >= 8.5 ? "from-red-500 to-orange-500" : score >= 7 ? "from-amber-500 to-yellow-500" : score >= 5 ? "from-blue-500 to-cyan-500" : "from-slate-500 to-gray-500";
  const s = size === "lg" ? "w-14 h-14 text-lg" : size === "sm" ? "w-8 h-8 text-[10px]" : "w-10 h-10 text-sm";
  return <div className={`${s} rounded-xl bg-gradient-to-br ${g} flex items-center justify-center font-bold text-white shadow-lg flex-shrink-0`}>{score.toFixed(1)}</div>;
}

export function StatCard({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className={`rounded-2xl p-5 ${accent ? "bg-gradient-to-br from-amber-500/15 to-orange-600/5 border border-amber-500/20" : "bg-[#1a1f35]/80 border border-white/5"}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{label}</p>
          <p className={`text-2xl font-bold ${accent ? "text-amber-400" : "text-white"}`}>{value}</p>
          {sub && <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-xl ${accent ? "bg-amber-500/15" : "bg-white/5"}`}>
          <Icon size={18} className={accent ? "text-amber-400" : "text-slate-500"} />
        </div>
      </div>
    </div>
  );
}

export function ObraCard({ obra, onClick }) {
  const tc = TIPO_STYLE[obra.tipo] || TIPO_STYLE.residencial;
  const FI = FONTE_ICON[obra.fonte] || Building2;
  return (
    <div onClick={() => onClick?.(obra)} className="group bg-[#1a1f35]/80 border border-white/5 rounded-2xl p-4 hover:border-cyan-500/20 transition-all cursor-pointer">
      <div className="flex gap-3">
        <ScoreBadge score={obra.score} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-white font-semibold text-[13px] leading-tight truncate group-hover:text-cyan-400 transition-colors">{obra.titulo}</h3>
            <ArrowUpRight size={13} className="text-slate-600 group-hover:text-cyan-400 flex-shrink-0 mt-0.5 transition-colors" />
          </div>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <span className="flex items-center gap-1 text-[11px] text-slate-400"><MapPin size={10} />{obra.cidade}-{obra.estado}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${tc}`}>{obra.tipo}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${STATUS_BG[obra.status]} text-white`}>{STATUS_LABEL[obra.status]}</span>
          </div>
          <div className="flex items-center gap-2.5 mt-1.5 text-[11px] text-slate-500">
            {obra.empresa && <span className="truncate max-w-[160px]">{obra.empresa}</span>}
            {obra.valor && <span className="text-emerald-400 font-medium">{fmt(obra.valor)}</span>}
            <span className="flex items-center gap-1 ml-auto"><FI size={9} />{obra.fonte.replace("_", " ")}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function MiniChart({ data }) {
  const max = Math.max(...data.map((d) => d.obras));
  return (
    <div className="flex items-end gap-1.5 h-16">
      {data.map((d, i) => (
        <div key={i} className="flex flex-col items-center gap-1 flex-1">
          <div className="w-full rounded-md bg-gradient-to-t from-cyan-500 to-cyan-400 min-h-[4px]" style={{ height: `${(d.obras / max) * 100}%`, opacity: 0.35 + (d.obras / max) * 0.65 }} />
          <span className="text-[9px] text-slate-600">{d.dia}</span>
        </div>
      ))}
    </div>
  );
}

export function FunnelBar({ data }) {
  const stages = [
    { k: "novo", l: "Novo", c: "bg-slate-500" }, { k: "enriquecido", l: "Enriquecido", c: "bg-blue-500" },
    { k: "contato_encontrado", l: "Contato", c: "bg-indigo-500" }, { k: "em_prospeccao", l: "Prospectando", c: "bg-amber-500" },
    { k: "convertido", l: "Convertido", c: "bg-emerald-500" },
  ];
  const mx = Math.max(...stages.map((s) => data[s.k] || 0));
  return (
    <div className="space-y-2">
      {stages.map((s) => { const v = data[s.k] || 0; return (
        <div key={s.k} className="flex items-center gap-2.5">
          <span className="text-[10px] text-slate-500 w-20 text-right">{s.l}</span>
          <div className="flex-1 h-4 bg-white/5 rounded-full overflow-hidden"><div className={`h-full ${s.c} rounded-full`} style={{ width: `${mx > 0 ? (v / mx) * 100 : 0}%` }} /></div>
          <span className="text-[11px] text-white font-medium w-8">{v}</span>
        </div>
      ); })}
    </div>
  );
}

export function SourceBar({ data }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  const src = [
    { k: "google_maps", l: "Google Maps", c: "bg-cyan-500" }, { k: "diario_oficial", l: "Diários Oficiais", c: "bg-amber-500" },
    { k: "licitacao", l: "Licitações", c: "bg-purple-500" }, { k: "construtora", l: "Construtoras", c: "bg-emerald-500" },
  ];
  return (
    <div className="space-y-2.5">
      {src.map((s) => { const v = data[s.k] || 0; const p = total > 0 ? (v / total) * 100 : 0; return (
        <div key={s.k}>
          <div className="flex justify-between mb-1"><span className="text-[11px] text-slate-400">{s.l}</span><span className="text-[10px] text-slate-500">{v} ({p.toFixed(0)}%)</span></div>
          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden"><div className={`h-full ${s.c} rounded-full`} style={{ width: `${p}%` }} /></div>
        </div>
      ); })}
    </div>
  );
}

export function StateMap({ data }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const mx = entries[0]?.[1] || 1;
  return (
    <div className="grid grid-cols-5 gap-1.5">
      {entries.map(([e, c]) => (
        <div key={e} className="flex flex-col items-center p-2 rounded-lg border border-white/5 hover:border-cyan-500/20 transition cursor-pointer" style={{ background: `rgba(6,182,212,${(c / mx) * 0.25})` }}>
          <span className="text-[11px] font-bold text-white">{e}</span>
          <span className="text-[9px] text-slate-400">{c}</span>
        </div>
      ))}
    </div>
  );
}
