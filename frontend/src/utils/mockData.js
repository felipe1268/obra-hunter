export const MOCK_STATS = {
  total_obras: 1247, obras_novas_hoje: 23, obras_novas_semana: 156,
  total_empresas: 489, total_decisores: 312, decisores_validados: 87,
  buscas_ativas: 4, score_medio: 6.4,
  obras_por_status: { novo: 580, enriquecido: 340, contato_encontrado: 180, em_prospeccao: 89, convertido: 34, descartado: 24 },
  obras_por_tipo: { residencial: 520, comercial: 310, industrial: 145, infraestrutura: 172, institucional: 68, loteamento: 32 },
  obras_por_estado: { SP: 380, RJ: 195, MG: 148, PR: 95, SC: 82, RS: 78, BA: 72, GO: 58, PE: 52, CE: 47 },
  obras_por_fonte: { google_maps: 420, diario_oficial: 380, licitacao: 290, construtora: 157 },
  timeline: [
    { dia: "D", obras: 12 }, { dia: "S", obras: 28 }, { dia: "T", obras: 34 },
    { dia: "Q", obras: 22 }, { dia: "Q", obras: 31 }, { dia: "S", obras: 19 }, { dia: "S", obras: 23 },
  ],
};

export const MOCK_OBRAS = [
  { id: 1, titulo: "Edifício Corporate Plaza - Torre Sul", cidade: "São Paulo", estado: "SP", tipo: "comercial", fase: "fundacao", porte: "grande", score: 9.2, status: "novo", fonte: "google_maps", empresa: "Cyrela Brazil Realty", area: 12000, valor: 45000000 },
  { id: 2, titulo: "Condomínio Parque das Águas - Fase 2", cidade: "Campinas", estado: "SP", tipo: "residencial", fase: "estrutura", porte: "grande", score: 8.7, status: "enriquecido", fonte: "construtora", empresa: "MRV Engenharia", area: 8500, valor: 32000000 },
  { id: 3, titulo: "Centro Logístico Dutra - Galpões A-D", cidade: "Guarulhos", estado: "SP", tipo: "industrial", fase: "aprovacao", porte: "grande", score: 8.5, status: "novo", fonte: "diario_oficial", empresa: "GLP Capital Partners", area: 22000, valor: 65000000 },
  { id: 4, titulo: "Hospital Regional Norte Fluminense", cidade: "Campos", estado: "RJ", tipo: "institucional", fase: "fundacao", porte: "grande", score: 8.1, status: "contato_encontrado", fonte: "licitacao", empresa: "Governo RJ", area: 6000, valor: 28000000 },
  { id: 5, titulo: "Residencial Vista Bela - 3 Torres", cidade: "Belo Horizonte", estado: "MG", tipo: "residencial", fase: "aprovacao", porte: "medio", score: 7.8, status: "novo", fonte: "construtora", empresa: "Direcional", area: 4200, valor: 18000000 },
  { id: 6, titulo: "Shopping Center Vida Nova", cidade: "Curitiba", estado: "PR", tipo: "comercial", fase: "fundacao", porte: "grande", score: 9.0, status: "novo", fonte: "google_maps", empresa: "Multiplan", area: 35000, valor: 120000000 },
  { id: 7, titulo: "Pavimentação BR-101 Trecho Joinville", cidade: "Joinville", estado: "SC", tipo: "infraestrutura", fase: "estrutura", porte: "grande", score: 7.5, status: "enriquecido", fonte: "licitacao", empresa: "DNIT", area: null, valor: 42000000 },
  { id: 8, titulo: "Loteamento Eco Park - 200 lotes", cidade: "Ribeirão Preto", estado: "SP", tipo: "loteamento", fase: "aprovacao", porte: "medio", score: 7.2, status: "novo", fonte: "diario_oficial", empresa: "Alphaville", area: 180000, valor: 25000000 },
];

export const MOCK_NOTIFS = [
  { id: 1, tipo: "oportunidade_quente", prioridade: "urgente", titulo: "🔥 Oportunidade Quente! Score 9.2/10", msg: "Corporate Plaza - Torre Sul\n📍 São Paulo - SP\n🏢 Comercial · Fundação · R$ 45M", obra_id: 1, lida: false, data: "2025-03-08T10:30:00" },
  { id: 2, tipo: "oportunidade_quente", prioridade: "urgente", titulo: "🔥 Oportunidade Quente! Score 9.0/10", msg: "Shopping Vida Nova\n📍 Curitiba - PR\n🏢 Comercial · Fundação · R$ 120M", obra_id: 6, lida: false, data: "2025-03-08T07:00:00" },
  { id: 3, tipo: "nova_obra", prioridade: "alta", titulo: "⭐ Boa Oportunidade — Score 8.7/10", msg: "Parque das Águas\n📍 Campinas - SP\n🏢 Residencial · Estrutura", obra_id: 2, lida: false, data: "2025-03-08T08:15:00" },
  { id: 4, tipo: "busca_concluida", prioridade: "baixa", titulo: "🔍 Busca 'Comerciais SP/RJ' concluída", msg: "23 obras novas em 45s", obra_id: null, lida: true, data: "2025-03-08T06:30:00" },
  { id: 5, tipo: "decisor_encontrado", prioridade: "media", titulo: "👤 Decisor encontrado", msg: "Carlos Silva (Dir. Engenharia) — Corporate Plaza", obra_id: 1, lida: true, data: "2025-03-08T10:35:00" },
];

export const MOCK_BUSCAS = [
  { id: 1, nome: "Obras Comerciais SP/RJ", ativa: true, freq: "continua", obras: 342, alertas: 28, filtros: { estados: ["SP", "RJ"], tipos: ["comercial"] } },
  { id: 2, nome: "Licitações Infraestrutura", ativa: true, freq: "diaria", obras: 189, alertas: 15, filtros: { tipos: ["infraestrutura"], fontes: ["licitacao"] } },
  { id: 3, nome: "Residencial Grande Sul", ativa: true, freq: "diaria", obras: 267, alertas: 22, filtros: { estados: ["PR", "SC", "RS"], tipos: ["residencial"] } },
  { id: 4, nome: "Industrial Nacional", ativa: false, freq: "semanal", obras: 95, alertas: 8, filtros: { tipos: ["industrial"] } },
];

export const MOCK_USERS = [
  { id: 1, nome: "Administrador", email: "admin@obrahunter.com", role: "admin", ativo: true },
  { id: 2, nome: "João Silva", email: "joao@empresa.com", role: "vendedor", ativo: true },
  { id: 3, nome: "Maria Santos", email: "maria@empresa.com", role: "gerente", ativo: true },
  { id: 4, nome: "Pedro Oliveira", email: "pedro@empresa.com", role: "vendedor", ativo: true },
  { id: 5, nome: "Ana Costa", email: "ana@empresa.com", role: "vendedor", ativo: false },
];
