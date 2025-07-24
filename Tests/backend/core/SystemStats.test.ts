vi.mock('os', async (importOriginal) => {
  const actual = await importOriginal();
  return Object.assign({}, actual, {
    cpus: () => [
      { times: { idle: 100, user: 100, sys: 100, irq: 100, nice: 100 } },
      { times: { idle: 200, user: 200, sys: 200, irq: 200, nice: 200 } }
    ],
    totalmem: () => 1000,
    freemem: () => 400,
    uptime: () => 12345,
    loadavg: () => [0.1, 0.2, 0.3]
  });
});

const siMock = {
  cpuTemperature: vi.fn().mockResolvedValue({ main: 55 }),
  osInfo: vi.fn().mockResolvedValue({ platform: 'testOS' }),
  system: vi.fn().mockResolvedValue({ model: 'testModel' }),
  cpu: vi.fn().mockResolvedValue({ speed: 'fast' }),
  mem: vi.fn().mockResolvedValue({ total: 1000, free: 400 }),
  memLayout: vi.fn().mockResolvedValue([{ size: 1000 }]),
  graphics: vi.fn().mockResolvedValue({ controllers: [] }),
  diskLayout: vi.fn().mockResolvedValue([{ type: 'SSD' }]),
  fsSize: vi.fn().mockResolvedValue([{ size: 1000 }]),
  networkInterfaces: vi.fn().mockResolvedValue([{ iface: 'eth0' }]),
  battery: vi.fn().mockResolvedValue({ percent: 100 }),
  users: vi.fn().mockResolvedValue([{ user: 'test' }]),
  processes: vi.fn().mockResolvedValue({ list: [{ pid: 1 }] }),
  services: vi.fn().mockResolvedValue([{ name: 'nginx', running: true }])
};
vi.mock('systeminformation', async (importOriginal) => {
  const actual = await importOriginal();
  return Object.assign({}, actual, siMock);
});

import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as SystemStats from '../../../backend/src/core/SystemStats';

describe('SystemStats', () => {
  beforeEach(() => {
    Object.values(siMock).forEach(fn => fn.mockClear && fn.mockClear());
  });

  it('getSystemStats returns valid structure and values', async () => {
    const stats = await SystemStats.getSystemStats();
    expect(typeof stats.cpu).toBe('number');
    expect(typeof stats.memory).toBe('number');
    expect(typeof stats.temperature === 'number' || stats.temperature === null).toBe(true);
    expect(typeof stats.uptime).toBe('number');
    expect(Array.isArray(stats.load)).toBe(true);
  });

  it('getSystemStats handles temperature error gracefully', async () => {
    siMock.cpuTemperature.mockRejectedValueOnce(new Error('fail'));
    const stats = await SystemStats.getSystemStats();
    expect(stats.temperature).toBeNull();
  });

  it('getSystemInfo returns all expected fields', async () => {
    const info = await SystemStats.getSystemInfo();
    expect(info).toHaveProperty('osInfo');
    expect(info).toHaveProperty('cpu');
    expect(info).toHaveProperty('mem');
  }, 15000);

  it('getProcesses returns process list', async () => {
    const procs = await SystemStats.getProcesses();
    expect(procs).toHaveProperty('list');
    expect(Array.isArray(procs.list)).toBe(true);
  });

  it('getServices returns service info', async () => {
    const services = await SystemStats.getServices('nginx');
    expect(Array.isArray(services)).toBe(true);
    expect(services[0]).toHaveProperty('name');
  });
}); 