import { useEffect, useState } from "react";
import { ClipboardList, RefreshCw } from "lucide-react";
import { apiRequest } from "./api";

export default function AuditLogs({ token }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadLogs() {
    setLoading(true);
    setError("");

    try {
      const response = await apiRequest("/api/audit/", {
        method: "GET",
        token,
      });

      const items = Array.isArray(response)
        ? response
        : response.items || [];

      setLogs(items);
    } catch (err) {
      setError(err.message || "Unable to load audit logs.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs();
  }, [token]);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Audit Logs</h1>
          <p>Review recorded actions and their history.</p>
        </div>

        <button onClick={loadLogs} disabled={loading}>
          <RefreshCw size={16} />
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && <p role="alert">{error}</p>}

      {loading ? (
        <p>Loading audit records...</p>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th>Actor</th>
                <th>Details</th>
                <th>Timestamp</th>
              </tr>
            </thead>

            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{log.action}</td>
                  <td>{log.entity_type}</td>
                  <td>{log.entity_id}</td>
                  <td>{log.actor}</td>
                  <td>{log.details || "—"}</td>
                  <td>
                    {log.created_at
                      ? new Date(log.created_at).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}

              {logs.length === 0 && (
                <tr>
                  <td colSpan={7}>No audit records found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="audit-summary">
        <ClipboardList size={18} />
        <span>Total records loaded: {logs.length}</span>
      </div>
    </div>
  );
}