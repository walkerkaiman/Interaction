import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fetch from 'node-fetch';
import WebSocket from 'ws';
import { spawn } from 'child_process';

let serverProcess: any;
const BASE_URL = 'http://127.0.0.1:8000';
const WS_URL = 'ws://127.0.0.1:8000';

beforeAll(async () => {
  serverProcess = spawn('node', ['backend/dist/index.js'], { stdio: 'inherit' });
  await new Promise(res => setTimeout(res, 5000));
});

afterAll(() => {
  if (serverProcess) serverProcess.kill();
});

describe('WebSocket Events', () => {
  it('should receive initial all_modules event on connect', done => {
    const ws = new WebSocket(WS_URL);
    ws.on('error', () => {}); // Suppress connection reset errors
    ws.on('message', msg => {
      const data = JSON.parse(msg.toString());
      if (data.type === 'all_modules') {
        expect(Array.isArray(data.modules)).toBe(true);
        ws.close();
        done();
      }
    });
  });

  it('should receive system_stats events', done => {
    const ws = new WebSocket(WS_URL);
    ws.on('error', () => {}); // Suppress connection reset errors
    let gotStats = false;
    ws.on('message', msg => {
      const data = JSON.parse(msg.toString());
      if (data.type === 'system_stats') {
        gotStats = true;
        ws.close();
        expect(typeof data.cpu).toBe('number');
        done();
      }
    });
    setTimeout(() => {
      if (!gotStats) {
        ws.close();
        expect(gotStats).toBe(true);
        done();
      }
    }, 3000);
  });

  it('should emit module_lock, module_update, and module_unlock on settings change', done => {
    const ws = new WebSocket(WS_URL);
    ws.on('error', () => {}); // Suppress connection reset errors
    const events: string[] = [];
    ws.on('message', msg => {
      const data = JSON.parse(msg.toString());
      if (data.type === 'module_lock') events.push('lock');
      if (data.type === 'module_update') events.push('update');
      if (data.type === 'module_unlock') {
        events.push('unlock');
        ws.close();
        expect(events).toEqual(['lock', 'update', 'unlock']);
        done();
      }
    });
    ws.on('open', async () => {
      // Find a real module name
      const res = await fetch(`${BASE_URL}/modules`);
      const mods = await res.json();
      const mod = mods[0];
      await fetch(`${BASE_URL}/modules/${mod.name}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test: 'value' })
      });
    });
  });

  it('should emit module_mode event on mode change', done => {
    const ws = new WebSocket(WS_URL);
    ws.on('error', () => {}); // Suppress connection reset errors
    let gotMode = false;
    ws.on('message', msg => {
      const data = JSON.parse(msg.toString());
      if (data.type === 'module_mode') {
        gotMode = true;
        ws.close();
        expect(data).toHaveProperty('mode');
        done();
      }
    });
    ws.on('open', async () => {
      const res = await fetch(`${BASE_URL}/modules`);
      const mods = await res.json();
      const mod = mods[0];
      await fetch(`${BASE_URL}/modules/${mod.name}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'trigger' })
      });
    });
  });
}); 