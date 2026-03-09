import { Bell, X } from "lucide-react";
import { PRIOR_STYLE } from "../utils/helpers";

export default function NotificationPanel({ open, onClose, notifs, onMarkRead, onMarkAllRead }) {
  if (!open) return null;
  const naoLidas = notifs.filter((n) => !n.lida).length;

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <div className="absolute right-0 top-0 bottom-0 w-full max-w-md bg-[#0f1225] border-l border-white/10 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-white/5">
          <div className="flex items-center gap-3">
            <Bell size={18} className="text-cyan-400" />
            <h2 className="text-white font-semibold">Notificações</h2>
            {naoLidas > 0 && <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">{naoLidas}</span>}
          </div>
          <div className="flex items-center gap-2">
            {naoLidas > 0 && (
              <button onClick={onMarkAllRead} className="text-[11px] text-cyan-400 hover:text-cyan-300 px-2 py-1 rounded-lg hover:bg-white/5">Marcar todas lidas</button>
            )}
            <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/5 text-slate-400"><X size={16} /></button>
          </div>
        </div>

        <div className="overflow-y-auto h-[calc(100vh-72px)] p-3 space-y-2">
          {notifs.length === 0 && (
            <div className="text-center py-16">
              <Bell size={32} className="text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">Nenhuma notificação</p>
            </div>
          )}
          {notifs.map((n) => (
            <div
              key={n.id}
              onClick={() => !n.lida && onMarkRead(n.id)}
              className={`relative p-4 rounded-xl border-l-4 transition-all cursor-pointer ${PRIOR_STYLE[n.prioridade] || PRIOR_STYLE.media} ${n.lida ? "opacity-50" : "hover:translate-x-1"}`}
            >
              {!n.lida && <div className="absolute top-4 right-4 w-2 h-2 rounded-full bg-cyan-400" />}
              <p className="text-sm text-white font-medium pr-4">{n.titulo}</p>
              {n.msg && <p className="text-[11px] text-slate-400 mt-1 whitespace-pre-line leading-relaxed">{n.msg}</p>}
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-slate-600">
                  {new Date(n.data).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
                </span>
                {n.obra_id && <span className="text-[10px] text-cyan-400/60">Ver obra →</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
