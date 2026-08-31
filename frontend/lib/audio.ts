/** Encode an Int16 PCM chunk as a base64 string for transport over the WebSocket. */
export function int16ToBase64(chunk: Int16Array): string {
  const bytes = new Uint8Array(chunk.byteLength);
  bytes.set(new Uint8Array(chunk.buffer, chunk.byteOffset, chunk.byteLength));
  let binary = "";
  const STEP = 0x8000;
  for (let i = 0; i < bytes.length; i += STEP) {
    binary += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + STEP)));
  }
  return btoa(binary);
}