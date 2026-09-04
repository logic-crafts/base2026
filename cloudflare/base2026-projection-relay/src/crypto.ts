const encoder = new TextEncoder();

function toArrayBuffer(value: ArrayBuffer | ArrayBufferView): ArrayBuffer {
  if (value instanceof ArrayBuffer) return value;
  return new Uint8Array(value.buffer, value.byteOffset, value.byteLength).slice().buffer;
}
export function bytesToHex(value: ArrayBuffer | ArrayBufferView): string {
  const bytes = value instanceof ArrayBuffer
    ? new Uint8Array(value)
    : new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function hexToBytes(value: string): Uint8Array | null {
  if (!/^[a-f0-9]{64}$/iu.test(value)) return null;
  const result = new Uint8Array(value.length / 2);
  for (let index = 0; index < result.length; index += 1) {
    result[index] = Number.parseInt(value.slice(index * 2, index * 2 + 2), 16);
  }
  return result;
}

export async function sha256Hex(value: string | ArrayBuffer | ArrayBufferView): Promise<string> {
  const input = typeof value === "string" ? encoder.encode(value).buffer : toArrayBuffer(value);
  return bytesToHex(await crypto.subtle.digest("SHA-256", input));
}

export function buildAuthCanonical(input: {
  method: string;
  pathname: string;
  timestamp: string;
  nonce: string;
  contentSha256: string;
  contentLength: number;
}): string {
  return [
    "BASE2026-HMAC-V1",
    input.method.toUpperCase(),
    input.pathname,
    input.timestamp,
    input.nonce,
    input.contentSha256.toLowerCase(),
    String(input.contentLength),
  ].join("\n");
}

export async function signHmacHex(secret: string, canonical: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return bytesToHex(await crypto.subtle.sign("HMAC", key, encoder.encode(canonical)));
}

export async function verifyHmacHex(secret: string, canonical: string, providedHex: string): Promise<boolean> {
  if (secret.length < 32) return false;
  const signature = hexToBytes(providedHex);
  if (!signature) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  return crypto.subtle.verify("HMAC", key, toArrayBuffer(signature), encoder.encode(canonical));
}
