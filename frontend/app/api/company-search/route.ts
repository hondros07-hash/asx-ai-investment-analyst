import { NextRequest, NextResponse } from "next/server";
import { api, SearchResponse } from "../../../lib/research-api";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q")?.trim();

  if (!query) {
    return NextResponse.json(
      { results: [], error: "Search query is required." },
      { status: 400 }
    );
  }

  const result = await api<SearchResponse>(
    `/v1/companies/search?q=${encodeURIComponent(query)}`
  );

  if (result.error || !result.data) {
    return NextResponse.json(
      {
        results: [],
        error: result.error ?? "Company search is unavailable.",
      },
      { status: 502 }
    );
  }

  return NextResponse.json({
    results: result.data.results ?? [],
    error: null,
  });
}
