import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fetch from 'node-fetch';
import { spawn } from 'child_process';

let serverProcess: any;

const BASE_URL = 'http://127.0.0.1:8000';

beforeAll(async () => {
  // Start the backend server
  serverProcess = spawn('node', ['backend/dist/index.js'], { stdio: 'inherit' });
  // Wait for server to be ready
  await new Promise(res => setTimeout(res, 5000));
});

afterAll(() => {
  if (serverProcess) serverProcess.kill();
});

const endpoints = [
  { path: '/modules', expect: (data: any) => {
    expect(Array.isArray(data)).toBe(true);
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('name');
    }
  }},
  { path: '/api/interactions', expect: (data: any) => {
    expect(Array.isArray(data)).toBe(true);
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('input');
      expect(data[0]).toHaveProperty('output');
      expect(data[0].input).toHaveProperty('module');
      expect(data[0].output).toHaveProperty('module');
    }
  }},
  { path: '/api/log_levels', expect: (data: any) => {
    expect(Array.isArray(data)).toBe(true);
    expect(data).toContain('System');
  }},
  { path: '/api/system_info', expect: (data: any) => {
    expect(data).toHaveProperty('cpu');
    expect(data).toHaveProperty('osInfo');
    expect(data).toHaveProperty('mem');
  }},
  { path: '/api/status', expect: (data: any) => {
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('timestamp');
    expect(data).toHaveProperty('modules');
    expect(data).toHaveProperty('interactions');
  }}
];

describe('API Contract/Schema Validation', () => {
  endpoints.forEach(({ path, expect: expectFn }) => {
    it(`validates schema for ${path}`, async () => {
      const res = await fetch(`${BASE_URL}${path}`);
      expect(res.status).toBe(200);
      const data = await res.json();
      expectFn(data);
    });
  });
}); 