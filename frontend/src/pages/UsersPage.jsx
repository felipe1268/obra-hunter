import { UserPlus, Shield, Check, X } from "lucide-react";
import { ROLE_LABEL, ROLE_STYLE } from "../utils/helpers";

export default function UsersPage({ users }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">Gerencie os usuários que acessam o sistema</p>
        <button className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-semibold hover:opacity-90 flex items-center gap-2">
          <UserPlus size={15} /> Novo Usuário
        </button>
      </div>

      <div className="bg-[#1a1f35]/80 border border-white/5 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left px-5 py-3 text-[10px] uppercase tracking-wider text-slate-500 font-medium">Usuário</th>
              <th className="text-left px-5 py-3 text-[10px] uppercase tracking-wider text-slate-500 font-medium">Email</th>
              <th className="text-left px-5 py-3 text-[10px] uppercase tracking-wider text-slate-500 font-medium">Perfil</th>
              <th className="text-left px-5 py-3 text-[10px] uppercase tracking-wider text-slate-500 font-medium">Status</th>
              <th className="text-right px-5 py-3 text-[10px] uppercase tracking-wider text-slate-500 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition">
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                      {u.nome.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                    </div>
                    <span className="text-sm text-white font-medium">{u.nome}</span>
                  </div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-400">{u.email}</td>
                <td className="px-5 py-4">
                  <span className={`text-[10px] px-2 py-1 rounded-lg font-medium ${ROLE_STYLE[u.role]}`}>
                    <Shield size={10} className="inline mr-1" />{ROLE_LABEL[u.role]}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <span className={`flex items-center gap-1.5 text-xs ${u.ativo ? "text-emerald-400" : "text-red-400"}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${u.ativo ? "bg-emerald-400" : "bg-red-400"}`} />
                    {u.ativo ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  <button className={`text-xs px-3 py-1.5 rounded-lg transition ${u.ativo ? "bg-red-500/10 text-red-400 hover:bg-red-500/20" : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"}`}>
                    {u.ativo ? "Desativar" : "Ativar"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
