import { pbkdf2Sync, randomBytes, timingSafeEqual } from "crypto";

const PBKDF2_ITERS = 200_000;

function pbkdf2Hex(password: string, saltHex: string): string {
  const salt = Buffer.from(saltHex, "hex");
  const key = pbkdf2Sync(password, salt, PBKDF2_ITERS, 32, "sha256");
  return key.toString("hex");
}

export function hashPassword(password: string): string {
  const saltHex = randomBytes(16).toString("hex");
  const hashed = pbkdf2Hex(password, saltHex);
  return `pbkdf2_sha256$${PBKDF2_ITERS}$${saltHex}$${hashed}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  try {
    const raw = typeof stored === "string" ? stored.trim() : "";
    const parts = raw.split("$", 4);
    if (parts.length < 4 || parts[0] !== "pbkdf2_sha256") return false;
    const iters = parseInt(parts[1], 10);
    if (!Number.isInteger(iters) || iters < 1) return false;
    const saltHex = parts[2].trim();
    const expected = parts[3].trim();
    if (!saltHex || !expected) return false;
    const salt = Buffer.from(saltHex, "hex");
    if (salt.length !== 16) return false;
    const key = pbkdf2Sync(password, salt, iters, 32, "sha256");
    const candidate = key.toString("hex");
    if (candidate.length !== expected.length) return false;
    const a = Buffer.from(candidate, "utf8");
    const b = Buffer.from(expected, "utf8");
    if (a.length !== b.length) return false;
    return timingSafeEqual(a, b);
  } catch {
    return false;
  }
}
