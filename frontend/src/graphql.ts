const GRAPHQL_URL =
  (import.meta as unknown as { env: Record<string, string> }).env?.VITE_GRAPHQL_URL || "/graphql";

async function gql<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables })
  });
  const json = await res.json();
  if (json.errors?.length) {
    throw new Error(json.errors.map((e: { message: string }) => e.message).join("; ").slice(0, 500));
  }
  return json.data as T;
}

export async function createItinerary(input: Record<string, unknown>) {
  const data = await gql<{ createItinerary: import("./types").Itinerary }>(
    `mutation Create($input: TripRequestInput!) {
      createItinerary(input: $input) {
        id status summary generationTimeMs createdAt emailStatus
        flights { airline departure arrival price currency bookingUrl logoUrl }
        hotels { name description pricePerNight totalPrice currency rating websiteUrl imageUrl }
      }
    }`,
    { input }
  );
  return data.createItinerary;
}

export async function fetchItinerary(id: string) {
  const data = await gql<{ itinerary: import("./types").Itinerary | null }>(
    `query Get($id: String!) { itinerary(id: $id) { id status summary generationTimeMs emailStatus } }`,
    { id }
  );
  return data.itinerary;
}

export async function approveItinerary(input: Record<string, unknown>) {
  const data = await gql<{ approveItinerary: import("./types").Itinerary }>(
    `mutation Approve($input: ApproveEmailInput!) {
      approveItinerary(input: $input) { id status emailStatus }
    }`,
    { input }
  );
  return data.approveItinerary;
}

export async function fetchMetrics() {
  const data = await gql<{ metricsSummary: import("./types").MetricsSummary }>(
    `{ metricsSummary { count medianMs p95Ms errorRate } }`
  );
  return data.metricsSummary;
}
