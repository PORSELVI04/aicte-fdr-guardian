import { useCallback, useEffect, useState } from "react";
import {
  RefreshCw,
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
} from "lucide-react";

import { apiRequest } from "./api";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }) {
  const normalized = (status || "PENDING").toUpperCase();

  const className =
    normalized === "APPROVED"
      ? "active"
      : normalized === "REJECTED"
        ? "expired"
        : normalized === "NEEDS_CORRECTION"
          ? "upcoming"
          : "pending";

  return (
    <span className={`status-badge ${className}`}>
      {normalized.replaceAll("_", " ")}
    </span>
  );
}

export default function Reviews({ token }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submittingId, setSubmittingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [comments, setComments] = useState({});

  const loadReviews = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/api/reviews/", { token });

      setReviews(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Unable to load verification reviews.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  async function handleDecision(review, decision) {
    const reviewId = review.review_id;

    if (review.reviewer_decision !== "PENDING") {
      setError("This review has already received a decision.");
      return;
    }

    const actionLabel = decision.replaceAll("_", " ").toLowerCase();

    if (
      !window.confirm(
        `Confirm "${actionLabel}" for Review #${reviewId}?`
      )
    ) {
      return;
    }

    setSubmittingId(reviewId);
    setError("");
    setMessage("");

    try {
      await apiRequest(`/api/reviews/${reviewId}/decision`, {
        token,
        method: "PATCH",
        body: {
          decision,
          comments: comments[reviewId]?.trim() || null,
        },
      });

      setMessage(`Review #${reviewId} was marked ${actionLabel}.`);
      await loadReviews();
    } catch (err) {
      setError(err.message || "Unable to save the review decision.");
    } finally {
      setSubmittingId(null);
    }
  }

  const filteredReviews =
    filter === "ALL"
      ? reviews
      : reviews.filter(
          (review) => (review.reviewer_decision || "PENDING") === filter
        );

  const pendingCount = reviews.filter(
    (review) => (review.reviewer_decision || "PENDING") === "PENDING"
  ).length;

  return (
    <section className="content-card full-page-card">
      <div className="page-heading">
        <div>
          <p className="eyebrow">DOCUMENT REVIEW WORKFLOW</p>
          <h1>Verification Reviews</h1>
          <p className="muted">
            Review OCR discrepancies and record authorized decisions.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={loadReviews}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <div className="stat-icon blue">
            <ClipboardCheck size={22} />
          </div>
          <div className="stat-content">
            <p>Total Reviews</p>
            <h3>{reviews.length}</h3>
            <span>All verification records</span>
          </div>
        </article>

        <article className="stat-card">
          <div className="stat-icon orange">
            <AlertTriangle size={22} />
          </div>
          <div className="stat-content">
            <p>Pending Reviews</p>
            <h3>{pendingCount}</h3>
            <span>Awaiting a decision</span>
          </div>
        </article>
      </div>

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {message && (
        <div className="success-message" role="status">
          <CheckCircle2 size={18} />
          {message}
        </div>
      )}

      <div className="filter-row">
        <label htmlFor="review-filter">Filter reviews</label>

        <select
          id="review-filter"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        >
          <option value="ALL">All reviews</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="NEEDS_CORRECTION">Needs correction</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-state">
          <RefreshCw size={24} className="spin" />
          <p>Loading verification reviews...</p>
        </div>
      ) : filteredReviews.length === 0 ? (
        <div className="empty-state">
          <FileText size={25} />
          <p>No reviews found for this filter.</p>
        </div>
      ) : (
        <div className="review-list">
          {filteredReviews.map((review) => {
            const status = review.reviewer_decision || "PENDING";
            const isPending = status === "PENDING";
            const isSubmitting = submittingId === review.review_id;

            return (
              <article className="content-card" key={review.review_id}>
                <div className="section-header">
                  <div>
                    <h3>Review #{review.review_id}</h3>
                    <p className="muted">
                      FDR ID: {review.fdr_id} · Document ID:{" "}
                      {review.document_id}
                    </p>
                  </div>

                  <StatusBadge status={status} />
                </div>

                <div className="review-details">
                  <p>
                    <strong>Verification status:</strong>{" "}
                    {review.verification_status || "—"}
                  </p>

                  <p>
                    <strong>Created:</strong>{" "}
                    {formatDate(review.created_at)}
                  </p>

                  <p>
                    <strong>Reviewed by:</strong>{" "}
                    {review.reviewed_by || "Not reviewed"}
                  </p>
                </div>

                <div className="review-discrepancies">
                  <strong>Discrepancy details</strong>

                  {review.discrepancy_details?.length ? (
                    <ul>
                      {review.discrepancy_details.map((detail, index) => (
                        <li key={`${review.review_id}-${index}`}>
                          {detail}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">
                      No discrepancies recorded.
                    </p>
                  )}
                </div>

                {review.reviewer_comments && (
                  <div className="review-comments">
                    <strong>Reviewer comments</strong>
                    <p>{review.reviewer_comments}</p>
                  </div>
                )}

                {isPending && (
                  <div className="review-decision">
                    <label htmlFor={`comments-${review.review_id}`}>
                      Decision comments
                    </label>

                    <textarea
                      id={`comments-${review.review_id}`}
                      rows={3}
                      maxLength={2000}
                      placeholder="Enter comments or reasons for your decision..."
                      value={comments[review.review_id] || ""}
                      onChange={(event) =>
                        setComments((previous) => ({
                          ...previous,
                          [review.review_id]: event.target.value,
                        }))
                      }
                      disabled={isSubmitting}
                    />

                    <div className="review-actions">
                      <button
                        className="primary-button"
                        onClick={() => handleDecision(review, "APPROVED")}
                        disabled={isSubmitting}
                      >
                        <CheckCircle2 size={16} />
                        Approve
                      </button>

                      <button
                        className="secondary-button"
                        onClick={() =>
                          handleDecision(review, "NEEDS_CORRECTION")
                        }
                        disabled={isSubmitting}
                      >
                        <AlertTriangle size={16} />
                        Needs correction
                      </button>

                      <button
                        className="secondary-button"
                        onClick={() => handleDecision(review, "REJECTED")}
                        disabled={isSubmitting}
                      >
                        <XCircle size={16} />
                        Reject
                      </button>
                    </div>

                    {isSubmitting && (
                      <p className="muted">Saving decision...</p>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}