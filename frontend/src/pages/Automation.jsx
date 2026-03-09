import { Zap, Play, Pause } from "lucide-react";
import { fmtN } from "../utils/helpers";

function BuscaCard({ busca, onToggle }) {
  return (
    <div className={`rounded-2xl p-5 border transition-all ${busca.ativa ? "bg-[#1a1f35]/80 border-emerald-500/20" : "bg-[#1a1f35]/40 border-white/5 opacity-60"}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${busca.ativa ? "bg-emerald-400 animate-pulse" : "bg-slate-600"}`} />
          <h3 className="text-white font-semibold text-sm">{busca.nome}</h3>
        </div>
        <button onClick={() => onToggle(busca.id)} className={`p-1.5 rounded-lg transition ${busca.ativa ? "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20" : "bg-slate-700 text-slate-400 hover:bg-slate-600"}`}>
          {busca.ativa ? <Pause size={14} /> : <Play size={14} />}
        </button>
      </div>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-bold text-white">{fmtN(busca.obras)}</p>
          <p className="text-[10px] text-slate-500">Obras</p>
        </div>
        <div>
          <p className="text-lg font-bold text-amber-400">{busca.alertas}</p>
          <p className="text-[10px] text-slate-500">Alertas</p>
        </div>
        <div>
          <p className="text-[11px] text-slate-400 mt-1">{busca.freq === "continua" ? "30min" : busca.freq === "diaria" ? "1x/dia" : "1x/sem"}</p>
          <p className="text-[10px] text-slate-500">Freq.</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1 mt-3">
        {busca.filtros.estados?.map((e) => (
          <span key={e} className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">{e}</span>
        ))}
        {busca.filtros.tipos?.map((t) => (
          <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">{t}</span>
        ))}
        {busca.filtros.fontes?.map((f) => (
          <span key={f} className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">{f}</span>
        ))}
      </div>
    </div>
  );
}

export default function AutomationPage({ buscas, onToggle }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Buscas automáticas rodando 24/7. O robô encontra obras e te alerta no painel.</p>
        <button className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-semibold hover:opacity-90 flex items-center gap-2">
          <Zap size={15} /> Nova Busca
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {buscas.map((b) => <BuscaCard key={b.id} busca={b} onToggle={onToggle} />)}
      </div>

      <div className="bg-[#1a1f35]/60 border border-dashed border-white/10 rounded-2xl p-8 text-center">
        <Zap size={32} className="text-cyan-400/50 mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Configure novas buscas para expandir sua prospecção</p>
        <p className="text-slate-500 text-xs mt-1">Defina filtros, frequência e score mínimo para alertas</p>
      </div>
    </div>
  );
}
