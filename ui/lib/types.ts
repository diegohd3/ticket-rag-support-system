export type Ticket = {
  ticket_id: string;
  titulo: string;
  descripcion_problema: string;
  descripcion_solucion: string;
  categoria: string;
  prioridad: string;
  estado: string;
  fecha_creacion: string;
  fecha_cierre: string | null;
  tags: string[];
  usuario_creador: string;
  sistema_afectado: string;
  logs: Record<string, unknown>;
  causa_raiz: string | null;
  pasos_diagnostico: string | null;
  entorno: string | null;
  version_sistema: string | null;
  impacto: string | null;
  resuelto_exitosamente: boolean;
};

export type TicketListResponse = {
  items: Ticket[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
};

export type TicketUpdateResponse = {
  ticket: Ticket;
  embedding_refreshed: boolean;
  updated_fields: string[];
};

export type ChatSource = {
  ticket_id: string;
  titulo: string;
  categoria: string;
  prioridad: string;
  relevance_score: number;
  text_score: number;
  semantic_score: number;
  rerank_score: number | null;
};

export type ChatAskResponse = {
  query: string;
  applied_filters: Record<string, string>;
  answer: string;
  used_llm: boolean;
  confidence: number;
  evidence_ticket_ids: string[];
  results_count: number;
  sources: ChatSource[];
};

export type ApiErrorPayload = {
  code: string;
  message: string;
  request_id: string;
  details?: unknown;
};

export type AuthUser = {
  username: string;
  display_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  last_login_at: string | null;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
};
