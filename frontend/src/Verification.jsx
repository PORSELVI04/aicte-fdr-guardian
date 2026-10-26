import { useEffect, useState } from "react";
import { apiRequest } from "./api";

const inputStyle = {
  display: "block",
  width: "100%",
  boxSizing: "border-box",
  padding: 12,
  marginTop: 8,
  marginBottom: 18,
  border: "1px solid #d1d5db",
  borderRadius: 8,
  background: "white",
};

const buttonStyle = {
  padding: "11px 18px",
  marginRight: 10,
  marginBottom: 16,
  border: 0,
  borderRadius: 8,
  background: "#315ce8",
  color: "white",
  cursor: "pointer",
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: "#475569",
};

const resultStyle = {
  marginTop: 24,
  marginBottom: 24,
  padding: 20,
  border: "1px solid #dbe3f0",
  borderRadius: 12,
  background: "#f8fafc",
};

const preStyle = {
  padding: 12,
  overflowX: "auto",
  whiteSpace: "pre-wrap",
  overflowWrap: "anywhere",
  borderRadius: 8,
  background: "#eef2f7",
};

export default function Verification({ token }) {
  const [fdrs, setFdrs] = useState([]);
  const [fdrId, setFdrId] = useState("");
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [result, setResult] = useState(null);

  const [reviews, setReviews] = useState([]);
  const [reviewId, setReviewId] = useState("");
  const [decision, setDecision] = useState("NEEDS_CORRECTION");
  const [reviewComments, setReviewComments] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadFdrs() {
      try {
        const data = await apiRequest("/api/fdrs/", { token });
        setFdrs(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message);
      }
    }

    loadFdrs();
  }, [token]);

  async function loadReviews() {
    try {
      const data = await apiRequest("/api/reviews/", { token });
      const items = Array.isArray(data) ? data : [];
      setReviews(items);

      if (reviewId && !items.some((item) => item.review_id === Number(reviewId) || item.id === Number(reviewId))) {
        setReviewId("");
      }
    } catch (err) {
      setError(`Unable to load review history: ${err.message}`);
    }
  }

  async function uploadDocument() {
    if (!fdrId || !file) {
      setError("Select an FDR record and a document first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setResult(null);
    setDocumentId(null);
    setReviewId("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const data = await apiRequest(`/api/fdrs/${fdrId}/documents`, {
        token,
        method: "POST",
        body: formData,
        isFormData: true,
      });

      setDocumentId(data.document_id ?? data.id);
      setMessage(`Document uploaded successfully. Document ID: ${data.document_id ?? data.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function runVerification() {
    if (!fdrId || !documentId) {
      setError("Upload a document before running OCR verification.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await apiRequest(
        `/api/fdrs/${fdrId}/documents/${documentId}/verify`,
        { token, method: "POST" }
      );

      setResult(data);
      setMessage("OCR verification completed. Review the extracted fields and discrepancies below.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function createReview() {
    if (!result || !fdrId || !documentId) {
      setError("Run OCR verification before creating a review.");
      return;
    }

    const issues = Array.isArray(result.issues) ? result.issues : [];

    const discrepancyDetails = issues.length
      ? issues
      : result.verification_status === "OCR_MATCHED"
        ? ["OCR comparison completed. Human review is still required before final authorization."]
        : ["Manual verification is required for the extracted document fields."];

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await apiRequest("/api/reviews/", {
        token,
        method: "POST",
        body: {
          fdr_id: Number(fdrId),
          document_id: Number(documentId),
          verification_status: result.verification_status || "REVIEW_REQUIRED",
          discrepancy_details: discrepancyDetails,
        },
      });

      const createdId = data.review_id ?? data.id;
      setReviewId(createdId ? String(createdId) : "");
      setMessage(
        createdId
          ? `Review created successfully. Review ID: ${createdId}`
          : "Review created successfully."
      );

      await loadReviews();
    } catch (err) {
      setError(`Unable to create review: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function submitDecision() {
    if (!reviewId) {
      setError("Select a review from the review history first.");
      return;
    }

    if (!reviewComments.trim()) {
      setError("Enter reviewer comments before submitting the decision.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await apiRequest(
        `/api/reviews/${reviewId}/decision`,
        {
          token,
          method: "PATCH",
          body: {
            reviewer_decision: decision,
            reviewer_comments: reviewComments.trim(),
          },
        }
      );

      setMessage(
        `Decision saved successfully: ${data.reviewer_decision || decision}`
      );
      setReviewComments("");
      await loadReviews();
    } catch (err) {
      setError(
        `Unable to save decision: ${err.message}. Check the decision endpoint's required fields in Swagger.`
      );
    } finally {
      setLoading(false);
    }
  }

  const selectedFdr = fdrs.find((item) => String(item.id) === String(fdrId));

  const selectedReview = reviews.find(
    (item) =>
      String(item.review_id ?? item.id) === String(reviewId)
  );

  return (
    <section className="content-card full-page-card">
      <h1>Document Verification</h1>
      <p>Upload an FDR document, compare extracted fields, and manage reviewer decisions.</p>

      <div style={{ maxWidth: 850, marginTop: 28 }}>
        <label htmlFor="fdr-select">Select FDR record</label>
        <select
          id="fdr-select"
          value={fdrId}
          onChange={(event) => {
            setFdrId(event.target.value);
            setDocumentId(null);
            setResult(null);
            setFile(null);
            setError("");
            setMessage("");
          }}
          style={inputStyle}
        >
          <option value="">Choose an FDR</option>
          {fdrs.map((fdr) => (
            <option key={fdr.id} value={fdr.id}>
              {fdr.fdr_number} — {fdr.bank_name}
            </option>
          ))}
        </select>

        {selectedFdr && (
          <div style={resultStyle}>
            <strong>Selected FDR:</strong> {selectedFdr.fdr_number}
            <br />
            <strong>Bank:</strong> {selectedFdr.bank_name}
            <br />
            <strong>Registered amount:</strong>{" "}
            {selectedFdr.deposit_amount}
          </div>
        )}

        <label htmlFor="fdr-file">Choose a document (PNG or JPG for OCR)</label>
        <input
          id="fdr-file"
          type="file"
          accept=".png,.jpg,.jpeg,image/png,image/jpeg"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setDocumentId(null);
            setResult(null);
            setError("");
            setMessage("");
          }}
          style={inputStyle}
        />

        <button onClick={uploadDocument} disabled={loading} style={buttonStyle}>
          {loading ? "Processing..." : "Upload Document"}
        </button>

        <button
          onClick={runVerification}
          disabled={loading || !documentId}
          style={buttonStyle}
        >
          {loading ? "Processing..." : "Run OCR Verification"}
        </button>

        {error && (
          <p role="alert" style={{ color: "#b91c1c", marginTop: 16 }}>
            {error}
          </p>
        )}

        {message && (
          <p role="status" style={{ color: "#047857", marginTop: 16 }}>
            {message}
          </p>
        )}

        {result && (
          <div style={resultStyle}>
            <h2>Verification Results</h2>

            <p>
              <strong>Status:</strong>{" "}
              {result.verification_status ?? "Unknown"}
            </p>

            <h3>Extracted Fields</h3>
            <pre style={preStyle}>
              {JSON.stringify(result.extracted_fields ?? {}, null, 2)}
            </pre>

            <h3>Field Comparisons</h3>
            <pre style={preStyle}>
              {JSON.stringify(result.comparison ?? {}, null, 2)}
            </pre>

            <h3>Discrepancies</h3>
            {result.issues?.length ? (
              <ul>
                {result.issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            ) : (
              <p>No issues were returned by the verification API.</p>
            )}

            <button
              onClick={createReview}
              disabled={loading}
              style={buttonStyle}
            >
              {loading ? "Processing..." : "Create Review"}
            </button>

            <p style={{ fontSize: 13, color: "#64748b" }}>
              OCR matching is not proof of authenticity. Human review and
              authorized bank verification are required.
            </p>
          </div>
        )}

        <div style={resultStyle}>
          <h2>Reviewer Decision</h2>
          <p>Select a review created by the system, then record the reviewer's decision.</p>

          <button
            onClick={loadReviews}
            disabled={loading}
            style={secondaryButtonStyle}
          >
            Refresh Review History
          </button>

          <label htmlFor="review-select">Select review</label>
          <select
            id="review-select"
            value={reviewId}
            onChange={(event) => {
              setReviewId(event.target.value);
              setError("");
              setMessage("");
            }}
            style={inputStyle}
          >
            <option value="">Choose a review</option>
            {reviews.map((review) => {
              const id = review.review_id ?? review.id;
              return (
                <option key={id} value={id}>
                  Review #{id} — FDR #{review.fdr_id} —{" "}
                  {review.reviewer_decision || "PENDING"}
                </option>
              );
            })}
          </select>

          {selectedReview && (
            <div>
              <p>
                <strong>Verification status:</strong>{" "}
                {selectedReview.verification_status}
              </p>
              <p>
                <strong>Current decision:</strong>{" "}
                {selectedReview.reviewer_decision || "PENDING"}
              </p>
              <p>
                <strong>Discrepancies:</strong>
              </p>
              <pre style={preStyle}>
                {JSON.stringify(selectedReview.discrepancy_details ?? [], null, 2)}
              </pre>
            </div>
          )}

          <label htmlFor="decision">Reviewer decision</label>
          <select
            id="decision"
            value={decision}
            onChange={(event) => setDecision(event.target.value)}
            style={inputStyle}
          >
            <option value="APPROVED">APPROVED</option>
            <option value="NEEDS_CORRECTION">NEEDS_CORRECTION</option>
            <option value="REJECTED">REJECTED</option>
          </select>

          <label htmlFor="review-comments">Reviewer comments</label>
          <textarea
            id="review-comments"
            rows={4}
            value={reviewComments}
            onChange={(event) => setReviewComments(event.target.value)}
            placeholder="Explain the decision and any required corrections..."
            style={inputStyle}
          />

          <button
            onClick={submitDecision}
            disabled={loading || !reviewId}
            style={buttonStyle}
          >
            {loading ? "Saving..." : "Submit Decision"}
          </button>
        </div>

        <div style={resultStyle}>
          <h2>Review History</h2>

          <button
            onClick={loadReviews}
            disabled={loading}
            style={secondaryButtonStyle}
          >
            Load / Refresh History
          </button>

          {reviews.length === 0 ? (
            <p>No review records loaded yet. Click Load / Refresh History.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Review ID</th>
                    <th>FDR ID</th>
                    <th>Document ID</th>
                    <th>Verification</th>
                    <th>Decision</th>
                    <th>Comments</th>
                  </tr>
                </thead>
                <tbody>
                  {reviews.map((review) => (
                    <tr key={review.review_id ?? review.id}>
                      <td>{review.review_id ?? review.id}</td>
                      <td>{review.fdr_id}</td>
                      <td>{review.document_id}</td>
                      <td>{review.verification_status}</td>
                      <td>{review.reviewer_decision || "PENDING"}</td>
                      <td>{review.reviewer_comments || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
