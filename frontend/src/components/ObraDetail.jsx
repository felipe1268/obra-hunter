import { MapPin, X, Building2, CheckCircle, XCircle, Linkedin, Phone, Mail } from "lucide-react";
import { fmt } from "../utils/helpers";
import { ScoreBadge } from "./Shared";

const MOCK_DECISORES = [
  { nome: "Carlos Roberto Silva", cargo: "Diretor de Engenharia", score: 10 },
  { nome: "Ana Maria Fernandes", cargo: "Gerente de Compras", score: 8 },
  { nome: "Paulo Henrique Costa", cargo: "Coordenador de Obras", score: 7 },
];

export default function ObraDetail({ obra, onClose }) {
  if (!obra) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-[#0f1225] border border-white/10 rounded-3xl shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between p-6 bg-[#0f1225]/95 backdrop-blur border-b border-white/5">
          <div className="flex items-center gap-4">
            <ScoreBadge score={obra.score} size="lg" />
            <div>
              <h2 className="text-lg font-bold text-white">{obra.titulo}</h2>
              <p className="text-sm text-slate-400 flex items-center gap-1"><MapPin size={12} />{obra.cidade} - {obra.estado}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400"><X size={18} /></button>
        </div>

        <div className="p-6 space-y-6">
          {/* Info Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { l: "Tipo", v: obra.tipo, c: "text-cyan-400" },
              { l: "Fase", v: obra.fase, c: "text-amber-400" },
              { l: "Porte", v: obra.porte, c: "text-purple-400" },
              { l: "Valor Est.", v: fmt(obra.valor), c: "text-emerald-400" },
            ].map((x, i) => (
              <div key={i} className="bg-white/5 rounded-xl p-3 text-center">
                <p className="text-[9px] text-slate-500 uppercase tracking-wider">{x.l}</p>
                <p className={`text-sm font-semibold capitalize ${x.c}`}>{x.v}</p>
              </div>
            ))}
          </div>

          {/* Empresa */}
          {obra.empresa && (
            <div className="bg-white/5 rounded-xl p-4">
              <h3 className="text-[10px] uppercase tracking-wider text-slate-500 mb-3">Empresa</h3>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                  <Building2 size={18} className="text-cyan-400" />
                </div>
                <div>
                  <p className="text-white font-medium">{obra.empresa}</p>
                  <div className="flex gap-3 mt-1">
                    <span className="text-[11px] text-slate-400 flex items-center gap-1"><Mail size={10} /> contato@empresa.com</span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1"><Phone size={10} /> (11) 3456-7890</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Decisores */}
          <div>
            <h3 className="text-[10px] uppercase tracking-wider text-slate-500 mb-3">Decisores Sugeridos</h3>
            <div className="space-y-2">
              {MOCK_DECISORES.map((d, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-indigo-500/20 transition">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                      {d.nome.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                    </div>
                    <div>
                      <p className="text-sm text-white font-medium">{d.nome}</p>
                      <p className="text-[11px] text-slate-400">{d.cargo} · Score {d.score}/10</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20"><Linkedin size={14} /></button>
                    <button className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"><CheckCircle size={14} /></button>
                    <button className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20"><XCircle size={14} /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button className="flex-1 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold text-sm hover:opacity-90">Iniciar Prospecção</button>
            <button className="px-5 py-3 rounded-xl bg-white/5 text-slate-300 text-sm hover:bg-white/10 border border-white/10">Descartar</button>
          </div>
        </div>
      </div>
    </div>
  );
}
