import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fetch from 'node-fetch';
import { spawn } from 'child_process';

let serverProcess: any;
const BASE_URL = 'http://127.0.0.1:8000';

beforeAll(async () => {
  // Start the backend server (assumes it can be started with `node backend/src/index.js`)
  serverProcess = spawn('node', ['backend/dist/index.js'], { stdio: 'inherit' });
  // Wait for server to be ready (simple delay, replace with health check if needed)
  await new Promise(res => setTimeout(res, 5000));
});

afterAll(() => {
  if (serverProcess) serverProcess.kill();
});

describe('API Integration', () => {
  it('GET /modules returns a list of modules', async () => {
    const res = await fetch(`${BASE_URL}/modules`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty('name');
  });

  it('GET /api/status returns status info', async () => {
    const res = await fetch(`${BASE_URL}/api/status`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty('status');
  });

  it('POST /modules/:id/settings returns 404 for missing module', async () => {
    const res = await fetch(`${BASE_URL}/modules/notamodule/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ foo: 'bar' })
    });
    expect(res.status).toBe(404);
  });
}); 