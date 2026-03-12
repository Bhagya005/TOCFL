import { SignJWT, jwtVerify } from "jose";

const JWT_SECRET = process.env.JWT_SECRET || "tocfl-dev-secret-change-in-production";
const secret = new TextEncoder().encode(JWT_SECRET);

export type TokenPayload = { sub: string; username: string };

export async function encodeToken(userId: number, username: string): Promise<string> {
  return new SignJWT({ sub: String(userId), username })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .sign(secret);
}

export async function decodeToken(token: string): Promise<TokenPayload | null> {
  try {
    const { payload } = await jwtVerify(token, secret);
    return {
      sub: String(payload.sub),
      username: String(payload.username ?? ""),
    };
  } catch {
    return null;
  }
}

export function getTokenFromRequest(request: Request): string | null {
  const auth = request.headers.get("authorization");
  if (auth?.startsWith("Bearer ")) return auth.slice(7);
  return null;
}

export async function getCurrentUser(request: Request): Promise<{ id: number; username: string } | null> {
  const token = getTokenFromRequest(request);
  if (!token) return null;
  const payload = await decodeToken(token);
  if (!payload) return null;
  const id = parseInt(payload.sub, 10);
  if (Number.isNaN(id)) return null;
  return { id, username: payload.username };
}

export async function requireAuth(request: Request): Promise<{ id: number; username: string }> {
  const user = await getCurrentUser(request);
  if (!user) {
    throw new Response(JSON.stringify({ detail: "Not authenticated" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }
  return user;
}
