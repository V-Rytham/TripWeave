import type { TripFormValues } from "../types";

export function validateTrip(v: TripFormValues): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!v.origin || v.origin.trim().length < 2) errors.origin = "Origin is required (min 2 characters).";
  else if (v.origin.length > 100) errors.origin = "Origin must be at most 100 characters.";
  else if (/https?:\/\//i.test(v.origin)) errors.origin = "Origin must not contain URLs.";
  if (!v.destination || v.destination.trim().length < 2) errors.destination = "Destination is required (min 2 characters).";
  else if (v.destination.length > 100) errors.destination = "Destination must be at most 100 characters.";
  else if (/https?:\/\//i.test(v.destination)) errors.destination = "Destination must not contain URLs.";
  if (!v.outboundDate) errors.outboundDate = "Outbound date is required.";
  if (!v.returnDate) errors.returnDate = "Return date is required.";
  if (v.outboundDate && v.returnDate && v.returnDate <= v.outboundDate)
    errors.returnDate = "Return date must be after outbound date.";
  if (!(v.adults >= 1 && v.adults <= 9)) errors.adults = "Adults must be 1–9.";
  if (!(v.children >= 0 && v.children <= 9)) errors.children = "Children must be 0–9.";
  if (v.adults + v.children > 9) errors.children = "Total passengers must be at most 9.";
  if (v.hotelClass !== "" && v.hotelClass !== undefined && !(v.hotelClass! >= 2 && v.hotelClass! <= 5))
    errors.hotelClass = "Hotel class must be 2–5 stars.";
  if (v.userPrompt && v.userPrompt.length > 2000) errors.userPrompt = "Notes must be at most 2000 characters.";
  if (v.userPrompt && v.userPrompt.length > 0 && v.userPrompt.length < 10)
    errors.userPrompt = "Notes must be at least 10 characters if provided.";
  return errors;
}
