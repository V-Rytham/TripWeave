import { useEffect, useState } from "react";
import { approveItinerary, createItinerary, fetchMetrics } from "./graphql";
import type { Itinerary, MetricsSummary, TripFormValues } from "./types";
import TripForm from "./components/TripForm";
import { FlightCard, HotelCard } from "./components/Cards";
import { PerformancePanel, ReviewStep } from "./components/Panels";
import "./styles.css";

type Status = "idle" | "loading" | "success" | "error";

export default function App() {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);

  async function refreshMetrics() {
    try {
      setMetrics(await fetchMetrics());
    } catch {
      /* metrics optional */
    }
  }

  useEffect(() => {
    void refreshMetrics();
  }, []);

  async function onSubmit(v: TripFormValues) {
    setStatus("loading");
    setError("");
    setApproved(false);
    try {
      const input: Record<string, unknown> = {
        origin: v.origin.trim(),
        destination: v.destination.trim(),
        outboundDate: v.outboundDate,
        returnDate: v.returnDate,
        adults: v.adults,
        children: v.children,
        rooms: v.rooms
      };
      if (v.hotelClass !== "" && v.hotelClass !== undefined) input.hotelClass = v.hotelClass;
      if (v.userPrompt?.trim()) input.userPrompt = v.userPrompt.trim();
      const it = await createItinerary(input);
      setItinerary(it);
      setStatus("success");
      await refreshMetrics();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setStatus("error");
    }
  }

  async function onApprove(email: { fromEmail: string; toEmail: string; subject: string }) {
    if (!itinerary) return;
    setApproving(true);
    setError("");
    try {
      const updated = await approveItinerary({ itineraryId: itinerary.id, ...email });
      setItinerary({ ...itinerary, status: updated.status, emailStatus: updated.emailStatus });
      setApproved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  }

  return (
    <main className="container">
      <a className="skip" href="#results">
        Skip to results
      </a>
      <h1>AI Travel Agent</h1>
      <p className="muted">
        Generate flight + hotel options, review them, then explicitly approve before any email is sent.
      </p>

      <section aria-label="Request">
        <h2>1. Trip request</h2>
        <TripForm onSubmit={onSubmit} loading={status === "loading"} />
      </section>

      <div id="results" tabIndex={-1}>
        {status === "loading" && <p role="status">Generating your itinerary…</p>}
        {status === "error" && (
          <p role="alert" className="error">
            Request failed: {error}
          </p>
        )}
        {status === "success" && itinerary && (
          <>
            <section aria-label="Results">
              <h2>2. Options</h2>
              {itinerary.flights.length === 0 && itinerary.hotels.length === 0 ? (
                <p>No structured options returned; see summary below.</p>
              ) : (
                <>
                  <h3>Flights</h3>
                  <div className="cards">
                    {itinerary.flights.map((f) => (
                      <FlightCard key={f.airline + f.departure} f={f} />
                    ))}
                  </div>
                  <h3>Hotels</h3>
                  <div className="cards">
                    {itinerary.hotels.map((h) => (
                      <HotelCard key={h.name} h={h} />
                    ))}
                  </div>
                </>
              )}
            </section>
            <ReviewStep itinerary={itinerary} onApprove={onApprove} approving={approving} />
            {approved && (
              <p role="status" className="success">
                Approved — email status: {itinerary.emailStatus}
              </p>
            )}
          </>
        )}
        {status === "idle" && <p className="muted">No results yet. Submit a trip request to begin.</p>}
      </div>

      <PerformancePanel currentMs={itinerary?.generationTimeMs ?? null} agg={metrics} />
    </main>
  );
}
