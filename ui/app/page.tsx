"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError, askChat, fetchTickets, patchTicket } from "@/lib/api";
import type { ChatAskResponse, Ticket } from "@/lib/types";

type UiError = {
  code: string;
  message: string;
  requestId: string;
};

function mapError(error: unknown): UiError {
  if (error instanceof ApiError) {
    return {
      code: error.code,
      message: error.message,
      requestId: error.requestId,
    };
  }
  return {
    code: "unknown_error",
    message: "Unexpected client-side error.",
    requestId: "n/a",
  };
}

export default function HomePage() {
  const [apiKey, setApiKey] = useState("");
  const [activeError, setActiveError] = useState<UiError | null>(null);

  const [userIdInput, setUserIdInput] = useState("");
  const [userNameInput, setUserNameInput] = useState("");
  const [sessionUserId, setSessionUserId] = useState("");
  const [sessionUserName, setSessionUserName] = useState("");

  const [chatQuery, setChatQuery] = useState("Users get ERR-401 when logging into support portal");
  const [chatTopK, setChatTopK] = useState(5);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResult, setChatResult] = useState<ChatAskResponse | null>(null);

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ticketsTotal, setTicketsTotal] = useState(0);
  const [ticketsOffset, setTicketsOffset] = useState(0);
  const [ticketsLimit] = useState(5);
  const [ticketsLoading, setTicketsLoading] = useState(false);

  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [editPriority, setEditPriority] = useState("");
  const [editSolution, setEditSolution] = useState("");
  const [saveLoading, setSaveLoading] = useState(false);

  const isIdentified = sessionUserId.trim().length > 0;

  useEffect(() => {
    const storedApiKey = window.localStorage.getItem("ui_api_key") ?? "";
    const storedUserId = window.localStorage.getItem("ui_user_id") ?? "";
    const storedUserName = window.localStorage.getItem("ui_user_name") ?? "";

    setApiKey(storedApiKey);
    setUserIdInput(storedUserId);
    setUserNameInput(storedUserName);
    setSessionUserId(storedUserId);
    setSessionUserName(storedUserName);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("ui_api_key", apiKey);
  }, [apiKey]);

  useEffect(() => {
    if (!isIdentified) {
      return;
    }
    void loadTickets(ticketsOffset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketsOffset, isIdentified]);

  const hasPrevious = ticketsOffset > 0;
  const hasNext = ticketsOffset + tickets.length < ticketsTotal;

  async function loadTickets(offset: number) {
    if (!isIdentified) {
      return;
    }
    setTicketsLoading(true);
    setActiveError(null);
    try {
      const payload = await fetchTickets({
        limit: ticketsLimit,
        offset,
        apiKey,
        userId: sessionUserId,
        userName: sessionUserName,
      });
      setTickets(payload.items);
      setTicketsTotal(payload.total);
      if (selectedTicket) {
        const refreshed = payload.items.find((item) => item.ticket_id === selectedTicket.ticket_id);
        if (refreshed) {
          selectTicket(refreshed);
        }
      }
    } catch (error) {
      setActiveError(mapError(error));
    } finally {
      setTicketsLoading(false);
    }
  }

  function selectTicket(ticket: Ticket) {
    setSelectedTicket(ticket);
    setEditTitle(ticket.titulo);
    setEditStatus(ticket.estado);
    setEditPriority(ticket.prioridad);
    setEditSolution(ticket.descripcion_solucion);
  }

  function onIdentify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedUserId = userIdInput.trim().toLowerCase();
    if (!normalizedUserId) {
      setActiveError({
        code: "user_identification_required",
        message: "User ID is required before using chat.",
        requestId: "client",
      });
      return;
    }

    setActiveError(null);
    setSessionUserId(normalizedUserId);
    setSessionUserName(userNameInput.trim());
    setTicketsOffset(0);
    setSelectedTicket(null);
    setChatResult(null);

    window.localStorage.setItem("ui_user_id", normalizedUserId);
    window.localStorage.setItem("ui_user_name", userNameInput.trim());
  }

  function onSignOut() {
    setSessionUserId("");
    setSessionUserName("");
    setChatResult(null);
    setTickets([]);
    setTicketsTotal(0);
    setSelectedTicket(null);
    setActiveError(null);
    window.localStorage.removeItem("ui_user_id");
    window.localStorage.removeItem("ui_user_name");
  }

  async function onSubmitChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isIdentified) {
      return;
    }
    setChatLoading(true);
    setActiveError(null);
    try {
      const response = await askChat({
        query: chatQuery,
        topK: chatTopK,
        apiKey,
        userId: sessionUserId,
        userName: sessionUserName || undefined,
      });
      setChatResult(response);
    } catch (error) {
      setActiveError(mapError(error));
    } finally {
      setChatLoading(false);
    }
  }

  async function onSaveTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTicket || !isIdentified) {
      return;
    }

    const body: Record<string, unknown> = {};
    if (editTitle !== selectedTicket.titulo) {
      body.titulo = editTitle;
    }
    if (editStatus !== selectedTicket.estado) {
      body.estado = editStatus;
    }
    if (editPriority !== selectedTicket.prioridad) {
      body.prioridad = editPriority;
    }
    if (editSolution !== selectedTicket.descripcion_solucion) {
      body.descripcion_solucion = editSolution;
    }
    body.auto_embed = true;

    setSaveLoading(true);
    setActiveError(null);
    try {
      const updated = await patchTicket({
        ticketId: selectedTicket.ticket_id,
        body,
        apiKey,
        userId: sessionUserId,
        userName: sessionUserName || undefined,
      });
      setSelectedTicket(updated.ticket);
      await loadTickets(ticketsOffset);
    } catch (error) {
      setActiveError(mapError(error));
    } finally {
      setSaveLoading(false);
    }
  }

  const selectedMeta = useMemo(() => {
    if (!selectedTicket) {
      return "No ticket selected.";
    }
    return `Ticket ${selectedTicket.ticket_id} • ${selectedTicket.categoria} • ${selectedTicket.sistema_afectado}`;
  }, [selectedTicket]);

  if (!isIdentified) {
    return (
      <main className="page">
        <section className="panel identify">
          <h1>Identify User Before Accessing Chat</h1>
          <p className="meta">
            This workspace requires user identification to enforce abuse controls and account
            blocking policies.
          </p>
          <form onSubmit={onIdentify} className="stack">
            <label className="field">
              <span>User ID (required)</span>
              <input
                value={userIdInput}
                onChange={(event) => setUserIdInput(event.target.value)}
                placeholder="example: maria.romero"
              />
            </label>
            <label className="field">
              <span>Display name (optional)</span>
              <input
                value={userNameInput}
                onChange={(event) => setUserNameInput(event.target.value)}
                placeholder="Maria Romero"
              />
            </label>
            <label className="field">
              <span>X-API-Key (optional)</span>
              <input
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="Only if backend requires internal API key"
              />
            </label>
            <button type="submit">Enter Workspace</button>
          </form>
          {activeError && (
            <section className="error">
              <strong>{activeError.code}</strong>
              <span>{activeError.message}</span>
              <span>request_id: {activeError.requestId}</span>
            </section>
          )}
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <h1>AI Support Ticket Chatbot</h1>
          <p>User: {sessionUserName || sessionUserId}</p>
        </div>
        <div className="stack">
          <label className="field inline">
            <span>X-API-Key (optional)</span>
            <input
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Paste API key only if backend requires it"
            />
          </label>
          <button type="button" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </header>

      {activeError && (
        <section className="error">
          <strong>{activeError.code}</strong>
          <span>{activeError.message}</span>
          <span>request_id: {activeError.requestId}</span>
        </section>
      )}

      <section className="grid">
        <article className="panel">
          <h2>Chat Console</h2>
          <form onSubmit={onSubmitChat} className="stack">
            <label className="field">
              <span>Issue query</span>
              <textarea
                value={chatQuery}
                onChange={(event) => setChatQuery(event.target.value)}
                minLength={3}
                required
              />
            </label>
            <label className="field short">
              <span>Top K</span>
              <input
                type="number"
                min={1}
                max={20}
                value={chatTopK}
                onChange={(event) => setChatTopK(Number(event.target.value))}
              />
            </label>
            <button type="submit" disabled={chatLoading}>
              {chatLoading ? "Running query..." : "Run Chat"}
            </button>
          </form>

          {chatResult && (
            <div className="result">
              <p className="meta">
                confidence={chatResult.confidence.toFixed(4)} • used_llm=
                {String(chatResult.used_llm)} • results={chatResult.results_count}
              </p>
              <p className="pre">{chatResult.answer}</p>
              <p className="meta">
                evidence: {chatResult.evidence_ticket_ids.join(", ") || "none"}
              </p>
              <div className="sources">
                <h3>Sources</h3>
                <ul>
                  {chatResult.sources.map((source) => (
                    <li key={source.ticket_id}>
                      {source.ticket_id} • {source.titulo} • score={source.relevance_score}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </article>

        <article className="panel">
          <h2>Tickets Workspace</h2>
          <div className="toolbar">
            <button
              type="button"
              disabled={ticketsLoading || !hasPrevious}
              onClick={() => setTicketsOffset((prev) => Math.max(0, prev - ticketsLimit))}
            >
              Previous
            </button>
            <button
              type="button"
              disabled={ticketsLoading || !hasNext}
              onClick={() => setTicketsOffset((prev) => prev + ticketsLimit)}
            >
              Next
            </button>
            <span className="meta">
              total={ticketsTotal} • offset={ticketsOffset} • limit={ticketsLimit}
            </span>
          </div>

          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Title</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr
                    key={ticket.ticket_id}
                    className={selectedTicket?.ticket_id === ticket.ticket_id ? "selected" : ""}
                    onClick={() => selectTicket(ticket)}
                  >
                    <td>{ticket.ticket_id}</td>
                    <td>{ticket.estado}</td>
                    <td>{ticket.prioridad}</td>
                    <td>{ticket.titulo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <form onSubmit={onSaveTicket} className="stack">
            <p className="meta">{selectedMeta}</p>
            <label className="field">
              <span>Title</span>
              <input
                value={editTitle}
                onChange={(event) => setEditTitle(event.target.value)}
                disabled={!selectedTicket}
              />
            </label>
            <div className="row">
              <label className="field">
                <span>Status</span>
                <input
                  value={editStatus}
                  onChange={(event) => setEditStatus(event.target.value)}
                  disabled={!selectedTicket}
                />
              </label>
              <label className="field">
                <span>Priority</span>
                <input
                  value={editPriority}
                  onChange={(event) => setEditPriority(event.target.value)}
                  disabled={!selectedTicket}
                />
              </label>
            </div>
            <label className="field">
              <span>Solution</span>
              <textarea
                value={editSolution}
                onChange={(event) => setEditSolution(event.target.value)}
                disabled={!selectedTicket}
              />
            </label>
            <button type="submit" disabled={!selectedTicket || saveLoading}>
              {saveLoading ? "Saving..." : "Save Ticket"}
            </button>
          </form>
        </article>
      </section>
    </main>
  );
}
