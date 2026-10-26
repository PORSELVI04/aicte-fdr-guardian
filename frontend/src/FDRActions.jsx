import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

export default function FDRActions({ token }) {
  const [actions, setActions] = useState([]);
  const [fdrId, setFdrId] = useState("1");
  const [actionType, setActionType] = useState("RENEWAL");
  const [remarks, setRemarks] = useState("");
  const [decisionRemarks, setDecisionRemarks] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function requestApi(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(options.body
          ? { "Content-Type": "application/json" }
          : {}),
        ...options.headers,
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || `Request failed (${response.status})`
      );
    }

    return data;
  }

  async function loadActions() {
    try {
      setLoading(true);
      setError("");

      const data = await requestApi("/api/fdr-actions/");
      setActions(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      loadActions();
    }
  }, [token]);

  async function createAction(event) {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      await requestApi("/api/fdr-actions/", {
        method: "POST",
        body: JSON.stringify({
          fdr_id: Number(fdrId),
          action_type: actionType,
          remarks: remarks.trim() || null,
        }),
      });

      setMessage("FDR action request created successfully.");
      setRemarks("");

      await loadActions();
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitDecision(actionId, status) {
    setMessage("");
    setError("");

    try {
      await requestApi(`/api/fdr-actions/${actionId}/decision`, {
        method: "PATCH",
        body: JSON.stringify({
          action_status: status,
          remarks: decisionRemarks[actionId]?.trim() || null,
        }),
      });

      setMessage(`Request #${actionId} marked ${status}.`);

      setDecisionRemarks((previous) => {
        const updated = { ...previous };
        delete updated[actionId];
        return updated;
      });

      await loadActions();
    } catch (err) {
      setError(err.message);
    }
  }

  function formatDate(dateValue) {
    if (!dateValue) {
      return "—";
    }

    const date = new Date(dateValue);

    return Number.isNaN(date.getTime())
      ? "—"
      : date.toLocaleString();
  }

  function hasDecisionMetadata(action) {
    return Boolean(action.decided_by && action.decided_at);
  }

  function getReviewStatus(action) {
    if (action.action_status === "PENDING") {
      return "Pending review";
    }

    return hasDecisionMetadata(action)
      ? "Decision recorded"
      : "Incomplete decision record";
  }

  function getDecisionLabel(action) {
    if (action.action_status === "PENDING") {
      return null;
    }

    return hasDecisionMetadata(action)
      ? "Decision recorded"
      : "Historical metadata unavailable";
  }

  return (
    <div className="page-container">
      <h1>FDR Actions</h1>

      <p>
        Manage requests for FDR renewal, replacement, and release.
      </p>

      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}

      <section className="card">
        <h2>Create FDR Action Request</h2>

        <form onSubmit={createAction}>
          <label htmlFor="fdrId">FDR ID</label>

          <input
            id="fdrId"
            type="number"
            min="1"
            step="1"
            value={fdrId}
            onChange={(event) => setFdrId(event.target.value)}
            required
          />

          <label htmlFor="actionType">Action Type</label>

          <select
            id="actionType"
            value={actionType}
            onChange={(event) => setActionType(event.target.value)}
          >
            <option value="RENEWAL">Renewal</option>
            <option value="REPLACEMENT">Replacement</option>
            <option value="RELEASE">Release</option>
          </select>

          <label htmlFor="remarks">Remarks</label>

          <textarea
            id="remarks"
            maxLength="1000"
            value={remarks}
            onChange={(event) => setRemarks(event.target.value)}
            placeholder="Enter the reason for this request"
          />

          <button type="submit" disabled={loading}>
            Create Request
          </button>
        </form>
      </section>

      <section className="card">
        <h2>FDR Action History</h2>

        <button onClick={loadActions} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>

        {!loading && actions.length === 0 ? (
          <p>No FDR action requests found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>FDR ID</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Remarks</th>
                  <th>Requested By</th>
                  <th>Created At</th>
                  <th>Review Status</th>
                  <th>Decided By</th>
                  <th>Decision Date</th>
                  <th>Decision</th>
                </tr>
              </thead>

              <tbody>
                {actions.map((action) => (
                  <tr key={action.id}>
                    <td>{action.id}</td>

                    <td>{action.fdr_id}</td>

                    <td>{action.action_type}</td>

                    <td>{action.action_status}</td>

                    <td>{action.remarks || "—"}</td>

                    <td>{action.performed_by || "Unknown"}</td>

                    <td>{formatDate(action.created_at)}</td>

                    <td>{getReviewStatus(action)}</td>

                    <td>{action.decided_by || "—"}</td>

                    <td>{formatDate(action.decided_at)}</td>

                    <td>
                      {action.action_status === "PENDING" ? (
                        <div>
                          <input
                            aria-label={`Review remarks for request ${action.id}`}
                            placeholder="Review remarks"
                            maxLength="1000"
                            value={decisionRemarks[action.id] || ""}
                            onChange={(event) =>
                              setDecisionRemarks((previous) => ({
                                ...previous,
                                [action.id]: event.target.value,
                              }))
                            }
                          />

                          <button
                            type="button"
                            onClick={() =>
                              submitDecision(action.id, "APPROVED")
                            }
                          >
                            Approve
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              submitDecision(action.id, "REJECTED")
                            }
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        getDecisionLabel(action)
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}