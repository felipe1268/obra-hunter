import { useState } from "react";
import { Filter, ChevronDown } from "lucide-react";
import { ObraCard } from "../components/Shared";

export default function ObrasPage({ obras, searchTerm, onObraClick }) {
  const [filterOpen, setFilterOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState("Todos");

  const filters = ["Todos", "Novos", "Enriquecidos", "Com Contato", "Prospectando"];

  const filtered = obras.filter((o) => {
    if (!searchTerm && activeFilter === "Todos") return true;
    const matchSearch = !searchTerm ||
      o.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.cidade.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.empresa?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchFilter = activeFilter === "Todos" ||
      (activeFilter === "Novos" && o.status === "novo") ||
      (activeFilter === "Enriquecidos" && o.status === "enriquecido") ||
      (activeFilter === "Com Contato" && o.status === "contato_encontrado") ||
      (activeFilter === "Prospectando" && o.status === "em_prospeccao");
    return matchSearch && matchFilter;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <button onClick={() => setFilterOpen(!filterOpen)} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-slate-300 hover:border-cyan-500/30">
          <Filter size={14} /> Filtros <ChevronDown size={12} />
        </button>
        {filters.map((f) => (
          <button key={f} onClick={() => setActiveFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs transition-all ${activeFilter === f ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "bg-white/5 text-slate-400 hover:text-white border border-transparent"}`}>
            {f}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">{filtered.length} resultados</span>
      </div>

      {filterOpen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-5 bg-[#1a1f35]/80 rounded-2xl border border-white/5">
          <div>
            <label className="text-[10px] uppercase text-slate-500 tracking-wider mb-2 block">Estado</label>
            <select className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50">
              <option value="">Todos</option>
              {["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "GO", "PE", "CE"].map((e) => <option key={e}>{e}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase text-slate-500 tracking-wider mb-2 block">Tipo</label>
            <select className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50">
              <option value="">Todos</option>
              {["residencial", "comercial", "industrial", "infraestrutura", "institucional", "loteamento"].map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase text-slate-500 tracking-wider mb-2 block">Fonte</label>
            <select className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50">
              <option value="">Todas</option>
              <option>google_maps</option><option>diario_oficial</option><option>licitacao</option><option>construtora</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase text-slate-500 tracking-wider mb-2 block">Score Mínimo</label>
            <input type="number" min="0" max="10" step="0.5" defaultValue="0" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50" />
          </div>
        </div>
      )}

      <div className="grid gap-3">
        {filtered.map((o) => <ObraCard key={o.id} obra={o} onClick={onObraClick} />)}
        {filtered.length === 0 && (
          <div className="text-center py-12">
            <p className="text-slate-500">Nenhuma obra encontrada com esses filtros</p>
          </div>
        )}
      </div>
    </div>
  );
}
