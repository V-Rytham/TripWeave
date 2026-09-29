import type { FlightOption, HotelOption } from "../types";

export function FlightCard({ f }: { f: FlightOption }) {
  return (
    <article className="card" aria-label={`Flight ${f.airline}`}>
      <h3>{f.airline}</h3>
      <p>
        {f.departure} → {f.arrival}
      </p>
      <p>
        <strong>
          {f.price} {f.currency}
        </strong>
      </p>
      {f.bookingUrl && (
        <a href={f.bookingUrl} target="_blank" rel="noreferrer">
          Book / source
        </a>
      )}
    </article>
  );
}

export function HotelCard({ h }: { h: HotelOption }) {
  return (
    <article className="card" aria-label={`Hotel ${h.name}`}>
      <h3>{h.name}</h3>
      <p>{h.description}</p>
      <p>
        {h.pricePerNight} {h.currency}/night · Total {h.totalPrice} {h.currency} · ⭐ {h.rating}
      </p>
      {h.websiteUrl && (
        <a href={h.websiteUrl} target="_blank" rel="noreferrer">
          Website / source
        </a>
      )}
    </article>
  );
}
