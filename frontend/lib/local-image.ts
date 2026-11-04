/** Decode an already-captured camera/file data URL without a network request.
 * Browser CSP intentionally restricts connect-src to 'self'; fetch(data:) is a
 * network operation and can fail with TypeError: Failed to fetch under that CSP.
 * The returned Blob is sent only by an explicit, consent-gated POST /build/media.
 */
const MAX_IMAGE_BYTES = 3 * 1024 * 1024;
const ALLOWED = new Set(['image/jpeg', 'image/png', 'image/webp']);

export function localImageToBlob(dataUrl: string): Blob {
  const match = /^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/]*={0,2})$/.exec(dataUrl);
  if (!match || !ALLOWED.has(match[1])) {
    throw new Error('Invalid local snapshot. Capture a new JPEG, PNG or WebP photo.');
  }
  const encoded = match[2];
  if (!encoded || encoded.length % 4 !== 0 || encoded.length > Math.ceil(MAX_IMAGE_BYTES / 3) * 4 + 4) {
    throw new Error('Snapshot must contain 1 byte to 3 MiB. Retake it at a lower resolution.');
  }
  let binary: string;
  try { binary = atob(encoded); }
  catch { throw new Error('Could not decode the snapshot. Retake the photo.'); }
  if (binary.length < 1 || binary.length > MAX_IMAGE_BYTES) {
    throw new Error('Snapshot must contain 1 byte to 3 MiB. Retake it at a lower resolution.');
  }
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: match[1] });
}
