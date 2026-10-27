import Verification from "./Verification";
import FDRActions from "./FDRActions";
import AuditLogs from "./AuditLogs";
import Reviews from "./Reviews";

import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Building2,
  FileText,
  ShieldCheck,
  Bell,
  Search,
  LogOut,
  Menu,
  X,
  RefreshCw,
  Wallet,
  Clock3,
  AlertTriangle,
  CheckCircle2,
  CircleDollarSign,
  FileCheck2,
  ClipboardList,
} from "lucide-react";

import { apiRequest, login } from "./api";
import "./App.css";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "FDR Records", icon: FileText },
  { label: "Institutions", icon: Building2 },
  { label: "Maturity Alerts", icon: Bell },
  { label: "Verification", icon: ShieldCheck },
  { label: "FDR Actions", icon: FileCheck2 },
  { label: "Reviews", icon: ClipboardList },
  { label: "Audit Logs", icon: ClipboardList },
];

function formatCurrency(value) {
  const amount = Number(value || 0);

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDate(value) {
  if (!value) return "—";

  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await login(username, password);
      await onLogin(result.access_token);
    } catch (err) {
      setError(err.message || "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-brand">
        <div className="brand-mark">
          <ShieldCheck size={34} />
        </div>

        <p className="eyebrow">SECURE DEPOSIT MANAGEMENT</p>

        <h1>
          AICTE FDR
          <br />
          Guardian
        </h1>

        <p className="login-description">
          One intelligent portal for managing fixed deposits, tracking
          maturity dates, and reviewing financial documents.
        </p>

        <div className="login-feature">
          <CheckCircle2 size={18} />
          Centralized FDR records
        </div>

        <div className="login-feature">
          <CheckCircle2 size={18} />
          Intelligent document review
        </div>

        <div className="login-feature">
          <CheckCircle2 size={18} />
          Timely maturity notifications
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={handleSubmit}>
          <div className="mobile-brand">
            <ShieldCheck size={28} />
            <span>AICTE FDR Guardian</span>
          </div>

          <p className="eyebrow">WELCOME BACK</p>
          <h2>Sign in to your account</h2>

          <p className="muted">
            Enter your authorized account credentials to continue.
          </p>

          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            placeholder="Enter your username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error && <div className="error-message">{error}</div>}

          <button className="primary-button login-button" disabled={loading}>
            {loading ? "Signing in..." : "Sign in securely"}
          </button>

          <p className="login-footnote">
            Access is restricted to authorized users.
          </p>
        </form>
      </section>
    </main>
  );
}

function StatCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <article className="stat-card">
      <div className={`stat-icon ${color}`}>
        <Icon size={22} />
      </div>

      <div className="stat-content">
        <p>{title}</p>
        <h3>{value}</h3>
        <span>{subtitle}</span>
      </div>
    </article>
  );
}

function Dashboard({
  summary,
  notifications,
  fdrs,
  institutions,
  onNavigate,
}) {
  const recentFdrs = [...fdrs]
    .sort((a, b) => (b.id || 0) - (a.id || 0))
    .slice(0, 5);

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">OVERVIEW</p>
          <h1>Dashboard</h1>
          <p className="muted">
            Monitor deposits, institution records, and upcoming maturities.
          </p>
        </div>

        <span className="date-chip">
          {new Date().toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </span>
      </div>

      <section className="stats-grid">
        <StatCard
          title="Total FDRs"
          value={summary?.total_fdrs ?? fdrs.length}
          subtitle="Registered deposits"
          icon={FileText}
          color="blue"
        />

        <StatCard
          title="Active FDRs"
          value={summary?.active_fdrs ?? "—"}
          subtitle="Not yet matured"
          icon={CheckCircle2}
          color="green"
        />

        <StatCard
          title="Expiring in 30 Days"
          value={notifications?.expiring_within_30_days_count ?? "—"}
          subtitle="Require timely attention"
          icon={Clock3}
          color="orange"
        />

        <StatCard
          title="Expired FDRs"
          value={notifications?.expired_count ?? "—"}
          subtitle="Check renewal or release"
          icon={AlertTriangle}
          color="red"
        />
      </section>

      <section className="summary-grid">
        <article className="deposit-card">
          <div className="deposit-card-top">
            <div>
              <span className="deposit-label">TOTAL DEPOSIT VALUE</span>
              <h2>{formatCurrency(summary?.total_deposit_amount)}</h2>
            </div>

            <div className="deposit-icon">
              <Wallet size={25} />
            </div>
          </div>

          <div className="deposit-footer">
            <span>
              <CircleDollarSign size={16} />
              Across all registered FDRs
            </span>

            <button
              className="text-button"
              onClick={() => onNavigate("FDR Records")}
            >
              View records →
            </button>
          </div>
        </article>

        <article className="institution-summary">
          <div className="section-title-row">
            <div className="small-icon">
              <Building2 size={20} />
            </div>

            <div>
              <h3>Institutions</h3>
              <p className="muted">Registered organizations</p>
            </div>
          </div>

          <div className="institution-count">{institutions.length}</div>

          <button
            className="secondary-button"
            onClick={() => onNavigate("Institutions")}
          >
            View institutions
          </button>
        </article>
      </section>

      <section className="content-card">
        <div className="section-header">
          <div>
            <h3>Recent FDR Records</h3>
            <p className="muted">
              Recently registered fixed deposit records
            </p>
          </div>

          <button
            className="text-button"
            onClick={() => onNavigate("FDR Records")}
          >
            View all →
          </button>
        </div>

        <FdrTable fdrs={recentFdrs} />
      </section>

      <section className="content-card alert-panel">
        <div className="section-header">
          <div>
            <h3>Maturity Alerts</h3>
            <p className="muted">Deposits requiring attention</p>
          </div>

          <button
            className="text-button"
            onClick={() => onNavigate("Maturity Alerts")}
          >
            View alerts →
          </button>
        </div>

        {notifications?.expired?.length > 0 ||
        notifications?.expiring_within_7_days?.length > 0 ? (
          <div className="alert-list">
            {(notifications?.expired || []).slice(0, 3).map((item) => (
              <div className="alert-row" key={`expired-${item.fdr_id}`}>
                <span className="alert-symbol red">
                  <AlertTriangle size={18} />
                </span>

                <div>
                  <strong>{item.fdr_number}</strong>
                  <p>Expired on {formatDate(item.maturity_date)}</p>
                </div>

                <span className="status-badge expired">Expired</span>
              </div>
            ))}

            {(notifications?.expiring_within_7_days || [])
              .slice(0, 3)
              .map((item) => (
                <div className="alert-row" key={`soon-${item.fdr_id}`}>
                  <span className="alert-symbol orange">
                    <Clock3 size={18} />
                  </span>

                  <div>
                    <strong>{item.fdr_number}</strong>
                    <p>Matures on {formatDate(item.maturity_date)}</p>
                  </div>

                  <span className="status-badge upcoming">
                    Expiring soon
                  </span>
                </div>
              ))}
          </div>
        ) : (
          <div className="empty-state">
            <CheckCircle2 size={24} />
            <p>
              {notifications
                ? "No expired or seven-day maturity alerts."
                : "Maturity alerts will appear when the backend is connected."}
            </p>
          </div>
        )}
      </section>
    </>
  );
}

function FdrTable({ fdrs }) {
  if (!fdrs.length) {
    return (
      <div className="empty-state">
        <FileText size={25} />
        <p>No FDR records found.</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>FDR Number</th>
            <th>Bank</th>
            <th>Amount</th>
            <th>Maturity Date</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {fdrs.map((fdr) => {
            // Released FDRs must never display as expired.
            const released = fdr.validity_status === "RELEASED";

            const expired =
              !released &&
              fdr.maturity_date &&
              fdr.maturity_date <
                new Date().toISOString().slice(0, 10);

            return (
              <tr key={fdr.id}>
                <td>
                  <strong>{fdr.fdr_number}</strong>
                </td>

                <td>{fdr.bank_name}</td>
                <td>{formatCurrency(fdr.deposit_amount)}</td>
                <td>{formatDate(fdr.maturity_date)}</td>

                <td>
                  <span
                    className={`status-badge ${
                      released
                        ? "released"
                        : expired
                          ? "expired"
                          : "active"
                    }`}
                  >
                    {released
                      ? "Released"
                      : expired
                        ? "Expired"
                        : fdr.validity_status || "Active"}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DataPage({ page, fdrs, institutions, notifications, token }) {
  const [search, setSearch] = useState("");

  useEffect(() => {
    setSearch("");
  }, [page]);

  if (page === "FDR Actions") {
    return <FDRActions token={token} />;
  }

  if (page === "Audit Logs") {
    return <AuditLogs token={token} />;
  }

  if (page === "Reviews") {
    return <Reviews token={token} />;
  }

  if (page === "FDR Records") {
    const filtered = fdrs.filter((fdr) =>
      [
        fdr.fdr_number,
        fdr.bank_name,
        fdr.branch_name,
        fdr.validity_status,
      ]
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase()),
    );

    return (
      <section className="content-card full-page-card">
        <div className="page-heading">
          <div>
            <h1>FDR Records</h1>
            <p className="muted">
              Search and review registered fixed deposits.
            </p>
          </div>
        </div>

        <div className="search-box">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search FDR number or bank..."
          />
        </div>

        <FdrTable fdrs={filtered} />
      </section>
    );
  }

  if (page === "Institutions") {
    const filtered = institutions.filter((institution) =>
      [
        institution.name,
        institution.institution_code,
        institution.contact_email,
      ]
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase()),
    );

    return (
      <section className="content-card full-page-card">
        <div className="page-heading">
          <div>
            <h1>Institutions</h1>
            <p className="muted">
              Registered institutions and contact information.
            </p>
          </div>
        </div>

        <div className="search-box">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search institution..."
          />
        </div>

        {filtered.length ? (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Institution Code</th>
                  <th>Institution Name</th>
                  <th>Email</th>
                  <th>Address</th>
                </tr>
              </thead>

              <tbody>
                {filtered.map((institution) => (
                  <tr key={institution.id}>
                    <td>{institution.institution_code}</td>
                    <td>
                      <strong>{institution.name}</strong>
                    </td>
                    <td>{institution.contact_email}</td>
                    <td>{institution.address}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <Building2 size={24} />
            <p>No institution records found.</p>
          </div>
        )}
      </section>
    );
  }

  if (page === "Maturity Alerts") {
    const groups = [
      {
        title: "Expired",
        items: notifications?.expired || [],
        style: "expired",
      },
      {
        title: "Expiring within 7 days",
        items: notifications?.expiring_within_7_days || [],
        style: "upcoming",
      },
      {
        title: "Expiring in 8–30 days",
        items: notifications?.expiring_in_8_to_30_days || [],
        style: "upcoming",
      },
    ];

    return (
      <section className="content-card full-page-card">
        <div className="page-heading">
          <div>
            <h1>Maturity Alerts</h1>
            <p className="muted">
              Review expired and upcoming deposit maturities.
            </p>
          </div>
        </div>

        {groups.map((group) => (
          <div className="alert-group" key={group.title}>
            <h3>
              {group.title}
              <span className="group-count">{group.items.length}</span>
            </h3>

            {group.items.length ? (
              group.items.map((item) => (
                <div className="alert-row" key={item.fdr_id}>
                  <span className={`alert-symbol ${group.style}`}>
                    {group.style === "expired" ? (
                      <AlertTriangle size={18} />
                    ) : (
                      <Clock3 size={18} />
                    )}
                  </span>

                  <div>
                    <strong>{item.fdr_number}</strong>
                    <p>
                      {item.bank_name} ·{" "}
                      {formatCurrency(item.deposit_amount)}
                    </p>
                    <p>Maturity: {formatDate(item.maturity_date)}</p>
                  </div>

                  <span className={`status-badge ${group.style}`}>
                    {group.title}
                  </span>
                </div>
              ))
            ) : (
              <p className="muted group-empty">
                No records in this category.
              </p>
            )}
          </div>
        ))}
      </section>
    );
  }

  if (page === "Verification") {
    return <Verification token={token} />;
  }

  return null;
}

export default function App() {
  const [token, setToken] = useState("");
  const [userRole, setUserRole] = useState("");
  const [activePage, setActivePage] = useState("Dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [summary, setSummary] = useState(null);
  const [notifications, setNotifications] = useState(null);
  const [fdrs, setFdrs] = useState([]);
  const [institutions, setInstitutions] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadWarning, setLoadWarning] = useState("");

  function decodeRole(accessToken) {
    try {
      const payload = accessToken.split(".")[1];
      const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
      const decoded = JSON.parse(atob(normalized));
      return decoded.role || "VIEWER";
    } catch {
      return "VIEWER";
    }
  }

  async function handleLogin(accessToken) {
    setToken(accessToken);
    setUserRole(decodeRole(accessToken));
  }

  async function loadData() {
    if (!token) return;

    setLoading(true);
    setError("");
    setLoadWarning("");

    const requests = await Promise.allSettled([
      apiRequest("/api/dashboard/summary", { token }),
      apiRequest("/api/notifications/maturity", { token }),
      apiRequest("/api/fdrs/", { token }),
      apiRequest("/api/institutions/", { token }),
    ]);

    let failures = 0;

    if (requests[0].status === "fulfilled") {
      setSummary(requests[0].value);
    } else {
      failures++;
    }

    if (requests[1].status === "fulfilled") {
      setNotifications(requests[1].value);
    } else {
      failures++;
    }

    if (requests[2].status === "fulfilled") {
      setFdrs(Array.isArray(requests[2].value) ? requests[2].value : []);
    } else {
      failures++;
    }

    if (requests[3].status === "fulfilled") {
      setInstitutions(
        Array.isArray(requests[3].value) ? requests[3].value : [],
      );
    } else {
      failures++;
    }

    if (failures) {
      setLoadWarning(
        `${failures} data request(s) failed. Check that the backend is running and the API routes are available.`,
      );
    }

    setLoading(false);
  }

  useEffect(() => {
    if (token) loadData();
  }, [token]);

  function handleLogout() {
    setToken("");
    setUserRole("");
    setActivePage("Dashboard");
    setSummary(null);
    setNotifications(null);
    setFdrs([]);
    setInstitutions([]);
    setError("");
    setLoadWarning("");
  }

  if (!token) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark small">
            <ShieldCheck size={25} />
          </div>

          <div>
            <strong>FDR Guardian</strong>
            <span>AICTE PORTAL</span>
          </div>

          <button
            className="icon-button mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        <p className="nav-caption">WORKSPACE</p>

        <nav className="sidebar-nav">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${
                activePage === label ? "nav-active" : ""
              }`}
              onClick={() => {
                setActivePage(label);
                setSidebarOpen(false);
                setError("");
              }}
            >
              <Icon size={19} />
              <span>{label}</span>

              {label === "Maturity Alerts" &&
                notifications?.expiring_within_30_days_count > 0 && (
                  <span className="nav-badge">
                    {notifications.expiring_within_30_days_count}
                  </span>
                )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="security-note">
            <ShieldCheck size={20} />
            <div>
              <strong>Secure workspace</strong>
              <p>Authorized access only</p>
            </div>
          </div>

          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button mobile-menu"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={22} />
            </button>

            <div className="breadcrumb">
              Workspace <span>/</span> <strong>{activePage}</strong>
            </div>
          </div>

          <div className="topbar-actions">
            <button
              className="icon-button refresh-button"
              onClick={loadData}
              disabled={loading}
              title="Refresh dashboard data"
              aria-label="Refresh data"
            >
              <RefreshCw
                size={18}
                className={loading ? "spin" : ""}
              />
            </button>

            <div className="user-avatar">{userRole.slice(0, 1) || "U"}</div>

            <div className="user-details">
              <strong>{userRole || "User"}</strong>
              <span>Portal account</span>
            </div>
          </div>
        </header>

        <div className="page-content">
          {loadWarning && (
            <div className="warning-banner">
              <AlertTriangle size={18} />
              {loadWarning}
              <button
                onClick={() => setLoadWarning("")}
                aria-label="Dismiss warning"
              >
                <X size={17} />
              </button>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          {loading && !summary && (
            <div className="loading-state">
              <RefreshCw size={24} className="spin" />
              <p>Loading FDR Guardian data...</p>
            </div>
          )}

          {activePage === "Dashboard" && (
            <Dashboard
              summary={summary}
              notifications={notifications}
              fdrs={fdrs}
              institutions={institutions}
              onNavigate={setActivePage}
            />
          )}

          {activePage !== "Dashboard" && (
            <DataPage
              page={activePage}
              fdrs={fdrs}
              institutions={institutions}
              notifications={notifications}
              token={token}
            />
          )}

          <footer className="app-footer">
            <span>AICTE FDR Guardian</span>
            <span>Financial Document Management Portal</span>
          </footer>
        </div>
      </main>
    </div>
  );
}