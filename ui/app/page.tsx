"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError, askChat, fetchTickets, login, patchTicket } from "@/lib/api";
import type { ChatAskResponse, Ticket } from "@/lib/types";

type UiError = {
  code: string;
  message: string;
  requestId: string;
};

type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

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

function getPriorityTone(priority: string): BadgeTone {
  const normalized = priority.toLowerCase();
  if (
    normalized.includes("alta") ||
    normalized.includes("high") ||
    normalized.includes("critical") ||
    normalized.includes("critica")
  ) {
    return "danger";
  }
  if (normalized.includes("media") || normalized.includes("medium")) {
    return "warning";
  }
  if (normalized.includes("baja") || normalized.includes("low")) {
    return "success";
  }
  return "neutral";
}

function getStatusTone(status: string): BadgeTone {
  const normalized = status.toLowerCase();
  if (
    normalized.includes("resuelto") ||
    normalized.includes("resolved") ||
    normalized.includes("cerrado") ||
    normalized.includes("closed")
  ) {
    return "success";
  }
  if (
    normalized.includes("open") ||
    normalized.includes("abierto") ||
    normalized.includes("pendiente") ||
    normalized.includes("investig")
  ) {
    return "warning";
  }
  return "info";
}

function badgeClass(tone: BadgeTone): string {
  return `badge badge-${tone}`;
}

function ErrorAlert({ error }: { error: UiError }) {
  return (
    <section className="alert alert-error" role="alert" aria-live="assertive">
      <div className="alert__title">{error.code}</div>
      <p>{error.message}</p>
      <p className="meta">request_id: {error.requestId}</p>
    </section>
  );
}

export default function HomePage() {
  const [activeError, setActiveError] = useState<UiError | null>(null);

  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  const [sessionAccessToken, setSessionAccessToken] = useState("");
  const [sessionUsername, setSessionUsername] = useState("");
  const [sessionDisplayName, setSessionDisplayName] = useState("");
  const [sessionIsAdmin, setSessionIsAdmin] = useState(false);

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

  const isAuthenticated = sessionAccessToken.trim().length > 0;

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }
    void loadTickets(ticketsOffset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketsOffset, isAuthenticated]);

  const hasPrevious = ticketsOffset > 0;
  const hasNext = ticketsOffset + tickets.length < ticketsTotal;

  function persistSession(params: {
    accessToken: string;
    username: string;
    displayName: string;
    isAdmin: boolean;
  }) {
    setSessionAccessToken(params.accessToken);
    setSessionUsername(params.username);
    setSessionDisplayName(params.displayName);
    setSessionIsAdmin(params.isAdmin);
  }

  function clearSession() {
    setSessionAccessToken("");
    setSessionUsername("");
    setSessionDisplayName("");
    setSessionIsAdmin(false);
    setPasswordInput("");

    setChatResult(null);
    setTickets([]);
    setTicketsTotal(0);
    setTicketsOffset(0);
    setSelectedTicket(null);
  }

  async function loadTickets(offset: number) {
    if (!isAuthenticated) {
      return;
    }
    setTicketsLoading(true);
    setActiveError(null);
    try {
      const payload = await fetchTickets({
        limit: ticketsLimit,
        offset,
        accessToken: sessionAccessToken,
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

  async function onLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginLoading(true);
    setActiveError(null);
    try {
      const response = await login({
        username: usernameInput,
        password: passwordInput,
      });
      persistSession({
        accessToken: response.access_token,
        username: response.user.username,
        displayName: response.user.display_name ?? "",
        isAdmin: response.user.is_admin,
      });
      setTicketsOffset(0);
      setSelectedTicket(null);
      setChatResult(null);
      setPasswordInput("");
    } catch (error) {
      setActiveError(mapError(error));
    } finally {
      setLoginLoading(false);
    }
  }

  function onSignOut() {
    clearSession();
    setActiveError(null);
  }

  async function onSubmitChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isAuthenticated) {
      return;
    }
    setChatLoading(true);
    setActiveError(null);
    try {
      const response = await askChat({
        query: chatQuery,
        topK: chatTopK,
        accessToken: sessionAccessToken,
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
    if (!selectedTicket || !isAuthenticated) {
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
        accessToken: sessionAccessToken,
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
    return `Ticket ${selectedTicket.ticket_id} | ${selectedTicket.categoria} | ${selectedTicket.sistema_afectado}`;
  }, [selectedTicket]);

  const hasTicketDraftChanges = useMemo(() => {
    if (!selectedTicket) {
      return false;
    }
    return (
      editTitle !== selectedTicket.titulo ||
      editStatus !== selectedTicket.estado ||
      editPriority !== selectedTicket.prioridad ||
      editSolution !== selectedTicket.descripcion_solucion
    );
  }, [editPriority, editSolution, editStatus, editTitle, selectedTicket]);

  const currentPage = Math.floor(ticketsOffset / ticketsLimit) + 1;
  const totalPages = Math.max(1, Math.ceil(ticketsTotal / ticketsLimit));

  if (!isAuthenticated) {
    return (
      <main className="app-shell app-shell--auth">
        <section className="auth-layout">
          <article className="card auth-brand">
            <p className="eyebrow">Support Intelligence Suite</p>
            <h1>AI Support Workspace</h1>
            <p className="auth-brand__copy">
              Unify support diagnostics, ticket intelligence and operational updates from one secure console.
            </p>
            <ul className="feature-list">
              <li>
                <strong>Faster triage</strong>
                <span>Surface the best historical incidents before escalating new cases.</span>
              </li>
              <li>
                <strong>Actionable context</strong>
                <span>Update ticket status, priority and solution notes without leaving the workspace.</span>
              </li>
              <li>
                <strong>Audit-ready flow</strong>
                <span>Error payloads include request IDs for traceability in backend observability tools.</span>
              </li>
            </ul>
          </article>

          <section className="card auth-panel" aria-labelledby="login-title">
            <div className="section-heading">
              <h2 id="login-title">Sign In</h2>
              <p>Access is restricted. Credentials are provisioned by a platform administrator.</p>
            </div>
            <form onSubmit={onLogin} className="form-stack">
              <label className="field">
                <span>Username</span>
                <input
                  value={usernameInput}
                  onChange={(event) => setUsernameInput(event.target.value)}
                  placeholder="example: maria.romero"
                  autoComplete="username"
                  required
                />
              </label>
              <label className="field">
                <span>Password</span>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(event) => setPasswordInput(event.target.value)}
                  placeholder="Your password"
                  autoComplete="current-password"
                  required
                  minLength={8}
                />
              </label>
              <button className="btn btn-primary btn-block" type="submit" disabled={loginLoading}>
                {loginLoading ? (
                  <>
                    <span className="spinner" aria-hidden="true" />
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </button>
            </form>

            {activeError && <ErrorAlert error={activeError} />}
          </section>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="card topbar">
        <div className="topbar__identity">
          <p className="eyebrow">Support Operations</p>
          <h1>AI Support Ticket Chatbot</h1>
          <p className="topbar__subtitle">
            Ask for incident context, inspect evidence and update ticket records in one workflow.
          </p>
        </div>
        <div className="topbar__controls">
          <div className="topbar__chips">
            <span className={badgeClass("info")}>{sessionDisplayName || sessionUsername}</span>
            <span className={badgeClass(sessionIsAdmin ? "warning" : "neutral")}>
              {sessionIsAdmin ? "Admin role" : "Standard role"}
            </span>
          </div>

          <button className="btn btn-ghost" type="button" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </header>

      <nav className="section-nav" aria-label="Workspace sections">
        <a href="#chat-console">Chat Console</a>
        <a href="#tickets-workspace">Tickets Workspace</a>
      </nav>

      {activeError && <ErrorAlert error={activeError} />}

      <section className="workspace-grid">
        <article id="chat-console" className="card section-card">
          <div className="section-heading">
            <h2>Chat Console</h2>
            <p>Ask natural language questions over the support incident knowledge base.</p>
          </div>

          <form onSubmit={onSubmitChat} className="form-stack">
            <label className="field">
              <span>Issue query</span>
              <textarea
                value={chatQuery}
                onChange={(event) => setChatQuery(event.target.value)}
                placeholder="Describe the user issue, symptoms or error code"
                minLength={3}
                required
              />
            </label>

            <div className="row row-chat">
              <label className="field field-compact">
                <span>Top K</span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={chatTopK}
                  onChange={(event) => {
                    const value = Number(event.target.value);
                    setChatTopK(Number.isFinite(value) ? value : 1);
                  }}
                />
              </label>

              <button className="btn btn-primary align-end" type="submit" disabled={chatLoading}>
                {chatLoading ? (
                  <>
                    <span className="spinner" aria-hidden="true" />
                    Running query...
                  </>
                ) : (
                  "Run Chat"
                )}
              </button>
            </div>
          </form>

          {chatLoading && (
            <p className="inline-status" aria-live="polite">
              <span className="spinner" aria-hidden="true" />
              Querying knowledge base...
            </p>
          )}

          {!chatLoading && !chatResult && (
            <section className="empty-state">
              <h3>No chat response yet</h3>
              <p>Run a query to get an AI-generated answer and ranked evidence tickets.</p>
            </section>
          )}

          {chatResult && (
            <div className="result-card">
              <div className="result-metrics">
                <span className="metric-pill">confidence {chatResult.confidence.toFixed(4)}</span>
                <span className="metric-pill">used_llm {String(chatResult.used_llm)}</span>
                <span className="metric-pill">results {chatResult.results_count}</span>
              </div>

              <p className="pre answer-text">{chatResult.answer}</p>
              <p className="meta">evidence: {chatResult.evidence_ticket_ids.join(", ") || "none"}</p>

              <div className="sources">
                <h3>Top Sources</h3>
                <ul className="source-list">
                  {chatResult.sources.length === 0 && (
                    <li className="source-item source-item--empty">No evidence sources returned.</li>
                  )}
                  {chatResult.sources.map((source) => {
                    const priorityTone = getPriorityTone(source.prioridad);
                    return (
                      <li key={source.ticket_id} className="source-item">
                        <div className="source-item__content">
                          <p className="source-item__title">
                            {source.ticket_id} | {source.titulo}
                          </p>
                          <p className="meta">{source.categoria}</p>
                        </div>
                        <span className={badgeClass(priorityTone)}>{source.prioridad}</span>
                        <span className="metric-pill">score {source.relevance_score.toFixed(3)}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          )}
        </article>

        <article id="tickets-workspace" className="card section-card">
          <div className="section-heading">
            <h2>Tickets Workspace</h2>
            <p>Browse incidents and edit selected ticket fields without leaving the dashboard.</p>
          </div>

          <div className="toolbar">
            <div className="toolbar__actions">
              <button
                className="btn btn-secondary"
                type="button"
                disabled={ticketsLoading || !hasPrevious}
                onClick={() => setTicketsOffset((prev) => Math.max(0, prev - ticketsLimit))}
              >
                Previous
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={ticketsLoading || !hasNext}
                onClick={() => setTicketsOffset((prev) => prev + ticketsLimit)}
              >
                Next
              </button>
            </div>
            <p className="meta">
              page {currentPage}/{totalPages} | total {ticketsTotal} | limit {ticketsLimit}
            </p>
          </div>

          {ticketsLoading && (
            <p className="inline-status" aria-live="polite">
              <span className="spinner" aria-hidden="true" />
              Loading tickets...
            </p>
          )}

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
                {tickets.length === 0 && (
                  <tr>
                    <td colSpan={4}>
                      <div className="table-empty">No tickets available for this page.</div>
                    </td>
                  </tr>
                )}

                {tickets.map((ticket) => {
                  const isSelectedRow = selectedTicket?.ticket_id === ticket.ticket_id;
                  const statusTone = getStatusTone(ticket.estado);
                  const priorityTone = getPriorityTone(ticket.prioridad);
                  return (
                    <tr
                      key={ticket.ticket_id}
                      className={isSelectedRow ? "selected" : ""}
                      onClick={() => selectTicket(ticket)}
                    >
                      <td>
                        <button
                          type="button"
                          className="table-select"
                          onClick={(event) => {
                            event.stopPropagation();
                            selectTicket(ticket);
                          }}
                          aria-pressed={isSelectedRow}
                        >
                          {ticket.ticket_id}
                        </button>
                      </td>
                      <td>
                        <span className={badgeClass(statusTone)}>{ticket.estado}</span>
                      </td>
                      <td>
                        <span className={badgeClass(priorityTone)}>{ticket.prioridad}</span>
                      </td>
                      <td className="title-cell">{ticket.titulo}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {!selectedTicket && (
            <section className="empty-state empty-state--compact">
              <h3>Select a ticket to edit</h3>
              <p>Choose a row above to enable the ticket editor and save field updates.</p>
            </section>
          )}

          <form onSubmit={onSaveTicket} className="form-stack editor-form">
            <div className="editor-head">
              <p className="meta">{selectedMeta}</p>
              {selectedTicket && (
                <span className={badgeClass(hasTicketDraftChanges ? "warning" : "success")}>
                  {hasTicketDraftChanges ? "Unsaved changes" : "Changes saved"}
                </span>
              )}
            </div>

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

            <button className="btn btn-primary" type="submit" disabled={!selectedTicket || saveLoading}>
              {saveLoading ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Saving...
                </>
              ) : (
                "Save Ticket"
              )}
            </button>
          </form>
        </article>
      </section>
    </main>
  );
}
