import type {
  ApiErrorPayload,
  ChatAskResponse,
  TicketListResponse,
  TicketUpdateResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string;
  readonly details: unknown;

  constructor(payload: ApiErrorPayload, status: number) {
    super(payload.message);
    this.name = "ApiError";
    this.status = status;
    this.code = payload.code;
    this.requestId = payload.request_id;
    this.details = payload.details;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  apiKey?: string;
  userId?: string;
  userName?: string;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (options.apiKey?.trim()) {
    headers["X-API-Key"] = options.apiKey.trim();
  }
  if (options.userId?.trim()) {
    headers["X-User-Id"] = options.userId.trim();
  }
  if (options.userName?.trim()) {
    headers["X-User-Name"] = options.userName.trim();
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const fallback: ApiErrorPayload = {
      code: "unknown_error",
      message: `Request failed with status ${response.status}`,
      request_id: "n/a",
    };
    let payload: ApiErrorPayload = fallback;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      // keep fallback when backend does not return JSON
    }
    throw new ApiError(payload, response.status);
  }

  return (await response.json()) as T;
}

export async function fetchTickets(params: {
  limit: number;
  offset: number;
  apiKey?: string;
  userId?: string;
  userName?: string;
}): Promise<TicketListResponse> {
  const query = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });
  return request<TicketListResponse>(`/api/v1/tickets?${query.toString()}`, {
    apiKey: params.apiKey,
    userId: params.userId,
    userName: params.userName,
  });
}

export async function patchTicket(params: {
  ticketId: string;
  body: Record<string, unknown>;
  apiKey?: string;
  userId?: string;
  userName?: string;
}): Promise<TicketUpdateResponse> {
  return request<TicketUpdateResponse>(`/api/v1/tickets/${params.ticketId}`, {
    method: "PATCH",
    body: params.body,
    apiKey: params.apiKey,
    userId: params.userId,
    userName: params.userName,
  });
}

export async function askChat(params: {
  query: string;
  topK: number;
  apiKey?: string;
  userId: string;
  userName?: string;
}): Promise<ChatAskResponse> {
  return request<ChatAskResponse>("/api/v1/chat/ask", {
    method: "POST",
    body: {
      query: params.query,
      top_k: params.topK,
    },
    apiKey: params.apiKey,
    userId: params.userId,
    userName: params.userName,
  });
}
