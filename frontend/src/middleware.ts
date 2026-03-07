import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Protect admin routes
  if (request.nextUrl.pathname.startsWith("/admin")) {
    const token = request.cookies.get("token")?.value;
    
    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    
    // Note: Actual admin role check should be done on the API side
    // This is just a basic protection layer
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: "/admin/:path*",
};
