// Aligned with backend GraphQL schema (strawberry -> camelCase).
export interface FlightOption {
  airline: string;
  departure: string;
  arrival: string;
  price: number;
  currency: string;
  bookingUrl?: string | null;
  logoUrl?: string | null;
}

export interface HotelOption {
  name: string;
  description: string;
  pricePerNight: number;
  totalPrice: number;
  currency: string;
  rating: number;
  websiteUrl?: string | null;
  imageUrl?: string | null;
}

export interface Itinerary {
  id: string;
  status: string;
  summary: string;
  flights: FlightOption[];
  hotels: HotelOption[];
  generationTimeMs: number;
  createdAt: string;
  emailStatus: string;
}

export interface MetricsSummary {
  count: number;
  medianMs: number;
  p95Ms: number;
  errorRate: number;
}

export interface TripFormValues {
  origin: string;
  destination: string;
  outboundDate: string;
  returnDate: string;
  adults: number;
  children: number;
  hotelClass?: number | "";
  rooms: number;
  userPrompt?: string;
}
