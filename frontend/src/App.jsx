import { useState, useEffect } from "react";
import { Building2, BarChart3, Bell, Zap, Users, Settings, Search, LogOut } from "lucide-react";
import { fmtN } from "./utils/helpers";
import { MOCK_STATS, MOCK_OBRAS, MOCK_NOTIFS, MOCK_BUSCAS, MOCK_USERS } from "./utils/mockData";

import LoginScreen from "./components/LoginScreen";
import NotificationPanel from "./components/NotificationPanel";
import ObraDetail from "./components/ObraDetail";
import DashboardPage from "./pages/Dashboard";
import ObrasPage from "./pages/ObrasList";
import AutomationPage from "./pages/Automation";
import UsersPage from "./pages/UsersPage";

const NAV = [
  { id: "dashboard", icon: BarChart3, label: "Dashboard" },
  { id: "obras", icon: Building2, label: "Obras" },
  { id: "buscas", icon: Zap, label: "Automação" },
  { id: "users", icon: Users, label: "Usuários" },
];

export default function App() {
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState("dashboard");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedObra, setSelectedObra] = useState(null);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifs, setNotifs] = useState(MOCK_NOTIFS);
  const [buscas, setBuscas] = useState(MOCK_BUSCAS);
  const [liveCount, setLiveCount] = useState(MOCK_STATS.total_obras);

  // Simular contador ao vivo
  useEffect(() => {
    if (!user) return;
    const i = setInterval(() => setLiveCount((c) => c + Math.floor(Math.random() * 3)), 8000);
    return () => clearInterval(i);
  }, [user]);

  // Simular nova notificação a cada 30s
  useEffect(() => {
    if (!user) return;
    const i = setInterval(() => {
      const newNotif = {
        id: Date.now(),
        tipo: "nova_obra",
        prioridade: Math.random() > 0.7 ? "urgente" : "alta",
        titulo: Math.random() > 0.7 ? "🔥 Nova oportunidade quente!" : "⭐ Nova obra encontrada",
        msg: `Obra ${Math.random() > 0.5 ? "comercial" : "residencial"} em ${["SP", "RJ", "MG", "PR"][Math.floor(Math.random() * 4)]}`,
        obra_id: null,
        lida: false,
        data: new Date().toISOString(),
      };
      setNotifs((prev) => [newNotif, ...prev]);
    }, 30000);
    return () => clearInterval(i);
  }, [user]);

  const naoLidas = notifs.filter((n) => !n.lida).length;

  const handleLogin = (u, token) => {
    setUser(u);
    localStorage.setItem("obrahunter_token", token);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("obrahunter_token");
  };

  const handleMarkRead = (id) => {
    setNotifs((prev) => prev.map((n) => n.id === id ? { ...n, lida: true } : n));
  };

  const handleMarkAllRead = () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, lida: true })));
  };

  const handleToggleBusca = (id) => {
    setBuscas((prev) => prev.map((b) => b.id === id ? { ...b, ativa: !b.ativa } : b));
  };

  // Login screen
  if (!user) return <LoginScreen onLogin={handleLogin} />;

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-slate-300">
      {/* SIDEBAR */}
      <aside className="fixed left-0 top-0 bottom-0 w-[220px] bg-[#0f1225] border-r border-white/5 flex flex-col z-40">
        <div className="p-5 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center">
              <Building2 size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-sm tracking-tight">ObraHunter</h1>
              <p className="text-[10px] text-slate-500">Prospecção automática</p>
            </div>
          </div>
        </div>

        {/* Live indicator */}
        <div className="mx-4 mt-4 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] text-emerald-400 font-medium">Buscando ao vivo</span>
          </div>
          <p className="text-lg font-bold text-white mt-1">{fmtN(liveCount)} <span className="text-xs font-normal text-slate-500">obras</span></p>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 mt-2">
          {NAV.map((item) => (
            <button key={item.id} onClick={() => setTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all mb-1 ${tab === item.id ? "bg-cyan-500/10 text-cyan-400 font-medium" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
              <item.icon size={17} />
              {item.label}
            </button>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
              {user.nome.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white font-medium truncate">{user.nome}</p>
              <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-slate-500 hover:bg-red-500/10 hover:text-red-400 transition">
            <LogOut size={14} /> Sair
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="ml-[220px] min-h-screen">
        {/* Header */}
        <header className="sticky top-0 z-30 bg-[#0a0e1a]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-white font-bold text-lg">{NAV.find((n) => n.id === tab)?.label}</h2>
              <p className="text-xs text-slate-500">Atualizado agora · {new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" placeholder="Buscar obras, empresas..."
                  value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-64 bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition" />
              </div>
              <button onClick={() => setNotifOpen(true)} className="relative p-2.5 rounded-xl bg-white/5 text-slate-400 hover:text-white border border-white/10 transition">
                <Bell size={17} />
                {naoLidas > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[8px] font-bold min-w-[18px] h-[18px] rounded-full flex items-center justify-center px-1">
                    {naoLidas > 99 ? "99+" : naoLidas}
                  </span>
                )}
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-6">
          {tab === "dashboard" && (
            <DashboardPage stats={MOCK_STATS} obras={MOCK_OBRAS} notifs={notifs} liveCount={liveCount} onObraClick={setSelectedObra} onTabChange={setTab} />
          )}
          {tab === "obras" && (
            <ObrasPage obras={MOCK_OBRAS} searchTerm={searchTerm} onObraClick={setSelectedObra} />
          )}
          {tab === "buscas" && (
            <AutomationPage buscas={buscas} onToggle={handleToggleBusca} />
          )}
          {tab === "users" && (
            <UsersPage users={MOCK_USERS} />
          )}
        </div>
      </main>

      {/* Overlays */}
      {selectedObra && <ObraDetail obra={selectedObra} onClose={() => setSelectedObra(null)} />}
      <NotificationPanel open={notifOpen} onClose={() => setNotifOpen(false)} notifs={notifs} onMarkRead={handleMarkRead} onMarkAllRead={handleMarkAllRead} />
    </div>
  );
}
