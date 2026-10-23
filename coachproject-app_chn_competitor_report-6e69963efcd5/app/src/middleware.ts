import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { decodeJWT } from "./app/utility/decoder";

export function middleware(req: NextRequest) {
  const pathname = req.nextUrl.pathname;
  const isAuthenticated = req.cookies.get("isAuthenticated")?.value;

  if (!isAuthenticated) {
    if (pathname !== "/") {
      return NextResponse.redirect(new URL("/", req.url));
    }
    return NextResponse.next();
  }

  let decoded;
  try {
    decoded = decodeJWT(isAuthenticated);
  } catch (error) {
    console.error("JWT Decoding Error:", error);
    return NextResponse.redirect(new URL("/", req.url));
  }

  if (!decoded || !decoded.exp || decoded.exp * 1000 < Date.now()) {
    req.cookies.delete("isAuthenticated");
    return NextResponse.redirect(new URL("/", req.url));
  }

  if (pathname === "/") {
    if (decoded.role === "admin") {
      return NextResponse.redirect(new URL("/list-uploader", req.url));
    } else if (decoded.role === "manager") {
      return NextResponse.redirect(new URL("/managers", req.url));
    }
  }

  if (pathname.startsWith("/list-uploader") && decoded.role !== "admin") {
    return NextResponse.redirect(new URL("/", req.url));
  }

  if (pathname.startsWith("/managers") && decoded.role !== "manager") {
    return NextResponse.redirect(new URL("/", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/list-uploader", "/managers/:path*"],
};
