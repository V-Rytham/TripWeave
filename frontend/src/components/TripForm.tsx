import { useState } from "react";
import type { TripFormValues } from "../types";
import { validateTrip } from "./validation";

const initial: TripFormValues = {
  origin: "Madrid",
  destination: "Paris",
  outboundDate: "",
  returnDate: "",
  adults: 2,
  children: 0,
  hotelClass: 4,
  rooms: 1,
  userPrompt: ""
};

export default function TripForm({ onSubmit, loading }: { onSubmit: (v: TripFormValues) => void; loading: boolean }) {
  const [values, setValues] = useState<TripFormValues>(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function set<K extends keyof TripFormValues>(k: K, val: TripFormValues[K]) {
    setValues((p) => ({ ...p, [k]: val }));
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validateTrip(values);
    setErrors(errs);
    if (Object.keys(errs).length === 0) onSubmit(values);
  }

  const field = (name: keyof TripFormValues, label: string, input: React.ReactNode, err?: string) => (
    <div className="field">
      <label htmlFor={`trip-${name}`}>{label}</label>
      {input}
      {err && (
        <p className="error" role="alert">
          {err}
        </p>
      )}
    </div>
  );

  return (
    <form onSubmit={submit} aria-label="Trip request form" noValidate>
      <div className="grid">
        {field(
          "origin",
          "Origin",
          <input id="trip-origin" value={values.origin} onChange={(e) => set("origin", e.target.value)} maxLength={100} required />,
          errors.origin
        )}
        {field(
          "destination",
          "Destination",
          <input id="trip-destination" value={values.destination} onChange={(e) => set("destination", e.target.value)} maxLength={100} required />,
          errors.destination
        )}
        {field(
          "outboundDate",
          "Outbound date",
          <input id="trip-outboundDate" type="date" value={values.outboundDate} onChange={(e) => set("outboundDate", e.target.value)} required />,
          errors.outboundDate
        )}
        {field(
          "returnDate",
          "Return date",
          <input id="trip-returnDate" type="date" value={values.returnDate} onChange={(e) => set("returnDate", e.target.value)} required />,
          errors.returnDate
        )}
        {field(
          "adults",
          "Adults (1–9)",
          <input id="trip-adults" type="number" min={1} max={9} value={values.adults} onChange={(e) => set("adults", Number(e.target.value))} />,
          errors.adults
        )}
        {field(
          "children",
          "Children (0–9)",
          <input id="trip-children" type="number" min={0} max={9} value={values.children} onChange={(e) => set("children", Number(e.target.value))} />,
          errors.children
        )}
        {field(
          "hotelClass",
          "Hotel stars (2–5)",
          <input
            id="trip-hotelClass"
            type="number"
            min={2}
            max={5}
            value={values.hotelClass}
            onChange={(e) => set("hotelClass", e.target.value === "" ? "" : Number(e.target.value))}
          />,
          errors.hotelClass
        )}
        {field(
          "rooms",
          "Rooms (1–5)",
          <input id="trip-rooms" type="number" min={1} max={5} value={values.rooms} onChange={(e) => set("rooms", Number(e.target.value))} />
        )}
      </div>
      <div className="field">
        <label htmlFor="trip-userPrompt">Extra preferences (optional, max 2000 chars)</label>
        <textarea
          id="trip-userPrompt"
          value={values.userPrompt}
          onChange={(e) => set("userPrompt", e.target.value)}
          maxLength={2000}
          rows={3}
        />
        {errors.userPrompt && (
          <p className="error" role="alert">
            {errors.userPrompt}
          </p>
        )}
      </div>
      <button type="submit" disabled={loading}>
        {loading ? "Generating itinerary…" : "Generate itinerary"}
      </button>
    </form>
  );
}
