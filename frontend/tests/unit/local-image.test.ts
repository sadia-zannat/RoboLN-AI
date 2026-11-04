import {test} from 'node:test';
import assert from 'node:assert/strict';
import {localImageToBlob} from '../../lib/local-image.ts';

test('camera data URL is converted to a JPEG Blob locally without fetch or CSP connect-src', async () => {
  const bytes = Uint8Array.from([255, 216, 255, 224, 0, 16, 74, 70, 73, 70, 0, 255, 217]);
  const oldFetch = globalThis.fetch;
  globalThis.fetch = (() => { throw new Error('Network fetch must not be used for captured photos'); }) as typeof fetch;
  try {
    const photo = localImageToBlob('data:image/jpeg;base64,' + Buffer.from(bytes).toString('base64'));
    assert.equal(photo.type, 'image/jpeg');
    assert.deepEqual(new Uint8Array(await photo.arrayBuffer()), bytes);
  } finally { globalThis.fetch = oldFetch; }
});

test('PNG and WebP local snapshots retain media type and exact bytes', async () => {
  for (const type of ['image/png', 'image/webp']) {
    const content = Buffer.from('nonempty test fixture');
    const photo = localImageToBlob(`data:${type};base64,${content.toString('base64')}`);
    assert.equal(photo.type, type);
    assert.deepEqual(Buffer.from(await photo.arrayBuffer()), content);
  }
});

test('invalid, empty and oversized data URLs are rejected before upload', () => {
  for (const bad of ['https://example.com/photo.jpg', 'data:image/svg+xml;base64,YQ==', 'data:image/jpeg;base64,', 'data:image/png;base64,!!', 'data:image/png;base64,' + Buffer.alloc(3 * 1024 * 1024 + 1, 0).toString('base64')]) {
    assert.throws(() => localImageToBlob(bad));
  }
});
