import { NextResponse } from "next/server";

const API_URL = process.env.AXIA_API_URL || "http://127.0.0.1:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params;
  const symbol = ticker.trim();

  if (!symbol) {
    return NextResponse.json(
      { error: "Ticker required" },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(
      `${API_URL}/v1/companies/${encodeURIComponent(symbol)}/identity`,
      {
        next: { revalidate: 3600 },
      }
    );

    if (!response.ok) {
      return NextResponse.json(
        { ticker: symbol, domain: null },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { ticker: symbol, domain: null },
      { status: 503 }
    );
  }
}
