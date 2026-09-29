import type { Itinerary, MetricsSummary } from "../types";

export function PerformancePanel({ currentMs, agg }: { currentMs: number | null; agg: MetricsSummary | null }) {
  return (
    <section aria-label="Performance panel" className="panel">
      <h2>Performance</h2>
      <p>
        Current itinerary generation:{" "}
        <strong>{currentMs === null ? "—" : `${currentMs.toFixed(1)} ms`}</strong>
      </p>
      {agg ? (
        <p>
          Recent (local): n={agg.count} · median {agg.medianMs.toFixed(1)} ms · p95 {agg.p95Ms.toFixed(1)} ms · errors{" "}
          {(agg.errorRate * 100).toFixed(1)}%
        </p>
      ) : (
        <p>No aggregate measurements yet.</p>
      )}
      <p className="muted">Measured with a monotonic clock; excludes email sending time.</p>
    </section>
  );
}

export function ReviewStep({
  itinerary,
  onApprove,
  approving
}: {
  itinerary: Itinerary;
  onApprove: (email: { fromEmail: string; toEmail: string; subject: string }) => void;
  approving: boolean;
}) {
  return (
    <section aria-label="Itinerary review" className="panel">
      <h2>Review before approval</h2>
      <p>{itinerary.summary}</p>
      <p className="muted">
        Status: {itinerary.status} · Email: {itinerary.emailStatus} · No email is sent until you approve below.
      </p>
      <ApproveForm onApprove={onApprove} approving={approving} />
    </section>
  );
}

import { useState } from "react";

function ApproveForm({
  onApprove,
  approving
}: {
  onApprove: (e: { fromEmail: string; toEmail: string; subject: string }) => void;
  approving: boolean;
}) {
  const [fromEmail, setFrom] = useState("");
  const [toEmail, setTo] = useState("");
  const [subject, setSubject] = useState("Your travel itinerary");
  const [err, setErr] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(fromEmail) || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(toEmail)) {
      setErr("Enter valid sender and recipient email addresses.");
      return;
    }
    setErr("");
    onApprove({ fromEmail, toEmail, subject });
  }

  return (
    <form onSubmit={submit} aria-label="Email approval form">
      <div className="grid">
        <div className="field">
          <label htmlFor="fromEmail">From email</label>
          <input id="fromEmail" type="email" value={fromEmail} onChange={(e) => setFrom(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="toEmail">To email</label>
          <input id="toEmail" type="email" value={toEmail} onChange={(e) => setTo(e.target.value)} required />
        </div>
      </div>
      <div className="field">
        <label htmlFor="subject">Subject</label>
        <input id="subject" value={subject} onChange={(e) => setSubject(e.target.value)} maxLength={200} required />
      </div>
      {err && (
        <p className="error" role="alert">
          {err}
        </p>
      )}
      <button type="submit" disabled={approving}>
        {approving ? "Sending…" : "Approve and send email"}
      </button>
    </form>
  );
}
