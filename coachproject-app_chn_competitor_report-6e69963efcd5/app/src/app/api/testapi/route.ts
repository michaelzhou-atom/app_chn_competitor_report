import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  return NextResponse.json(
    { error: 'Not Found' },
    { status: 404 }
  );
}
