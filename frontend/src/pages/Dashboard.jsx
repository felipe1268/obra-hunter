import { Building2, Zap, UserCheck, Star, ChevronRight, Bell } from "lucide-react";
import { fmtN } from "../utils/helpers";
import { StatCard, ObraCard, MiniChart, FunnelBar, SourceBar, StateMap, ScoreBadge } from "./Shared";

export default function DashboardPage({ stats, obras, notifs, liveCount, onObraClick, onTabChange }) {
  const topAlerts = notifs.filter(n => !n.lida && n.prioridade !== "baixa").slice(0, 4);

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Building2} label="Total de Obras" value={fmtN(liveCount)} sub={`+${stats.obras_novas_hoje} hoje`} />
        <StatCard icon={Zap} label="Buscas Ativas" value={stats.buscas_ativas} sub="Rodando 24/7" accent />
        <StatCard icon={UserCheck} label="Decisores" value={`${stats.decisores_validados}/${stats.total_decisores}`} sub="Validados" />
        <StatCard icon={Star} label="Score Médio" value={stats.score_medio.toFixed(1)} sub="De 0 a 10" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 md:col-span-4 bg-[#1a1f35]/80 border border-white/5 rounded-2xl p-5">
          <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-4">Obras · 7 dias</h3>
          <MiniChart data={stats.timeline} />
          <div className="flex justify-between mt-3">
            <span className="text-[10px] text-slate-500">Total semana</span>
            <span className="text-sm font-bold text-white">{stats.obras_novas_semana}</span>
          </div>
        </div>
        <div className="col-span-12 md:col-span-4 bg-[#1a1f35]/80 border border-white/5 rounded-2xl p-5">
          <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-4">Pipeline</h3>
          <FunnelBar data={stats.obras_por_status} />
        </div>
        <div className="col-span-12 md:col-span-4 bg-[#1a1f35]/80 border border-white/5 rounded-2xl p-5">
          <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-4">Fontes</h3>
          <SourceBar data={stats.obras_por_fonte} />
        </div>
      </div>

      {/* Map + Alerts */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 md:col-span-5 bg-[#1a1f35]/80 border border-white/5 rounded-2xl p-5">
          <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-4">Por Estado</h3>
          <StateMap data={stats.obras_por_estado} />
        </div>
        <div className="col-span-12 md:col-span-7 bg-[#1a1f35]/80 border border-white/5 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs uppercase tracking-wider text-slate-500">Alertas Recentes</h3>
            <Bell size={14} className="text-amber-400" />
          </div>
          <div className="space-y-2">
            {topAlerts.map((a) => (
              <div key={a.id} className="flex items-start gap-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10 cursor-pointer hover:border-amber-500/20 transition">
                <ScoreBadge score={parseFloat(a.titulo.match(/[\d.]+\/10/)?.[0] || "7")} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-white font-medium truncate">{a.titulo}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">{a.msg}</p>
                </div>
              </div>
            ))}
            {topAlerts.length === 0 && <p className="text-sm text-slate-600 text-center py-4">Sem alertas recentes</p>}
          </div>
        </div>
      </div>

      {/* Top Obras */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">Melhores Oportunidades</h3>
          <button onClick={() => onTabChange("obras")} className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1">Ver todas <ChevronRight size={12} /></button>
        </div>
        <div className="grid gap-3">
          {obras.slice(0, 4).map((o) => <ObraCard key={o.id} obra={o} onClick={onObraClick} />)}
        </div>
      </div>
    </div>
  );
}
