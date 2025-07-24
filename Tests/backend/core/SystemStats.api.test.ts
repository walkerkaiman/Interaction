import request from 'supertest';
import express from 'express';
import * as SystemStats from '../../../backend/src/core/SystemStats';

describe('SystemStats API endpoints', () => {
  let app: express.Express;

  beforeEach(() => {
    app = express();
    app.get('/api/system_info', async (req, res) => {
      try {
        const info = await SystemStats.getSystemInfo();
        res.json(info);
      } catch (err) {
        res.status(500).json({ error: 'Failed to get system info' });
      }
    });
    app.get('/api/processes', async (req, res) => {
      try {
        const procs = await SystemStats.getProcesses();
        res.json(procs);
      } catch (err) {
        res.status(500).json({ error: 'Failed to get processes' });
      }
    });
    app.get('/api/services', async (req, res) => {
      try {
        const names = req.query.names as string | undefined;
        const services = await SystemStats.getServices(names);
        res.json(services);
      } catch (err) {
        res.status(500).json({ error: 'Failed to get services' });
      }
    });
  });

  it('GET /api/system_info returns system info', async () => {
    vi.spyOn(SystemStats, 'getSystemInfo').mockResolvedValue({ foo: 'bar' });
    const res = await request(app).get('/api/system_info');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ foo: 'bar' });
  });

  it('GET /api/system_info handles error', async () => {
    vi.spyOn(SystemStats, 'getSystemInfo').mockRejectedValue(new Error('fail'));
    const res = await request(app).get('/api/system_info');
    expect(res.status).toBe(500);
    expect(res.body).toHaveProperty('error');
  });

  it('GET /api/processes returns processes', async () => {
    vi.spyOn(SystemStats, 'getProcesses').mockResolvedValue({ list: [1, 2, 3] });
    const res = await request(app).get('/api/processes');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ list: [1, 2, 3] });
  });

  it('GET /api/processes handles error', async () => {
    vi.spyOn(SystemStats, 'getProcesses').mockRejectedValue(new Error('fail'));
    const res = await request(app).get('/api/processes');
    expect(res.status).toBe(500);
    expect(res.body).toHaveProperty('error');
  });

  it('GET /api/services returns services', async () => {
    vi.spyOn(SystemStats, 'getServices').mockResolvedValue([{ name: 'nginx' }]);
    const res = await request(app).get('/api/services?names=nginx');
    expect(res.status).toBe(200);
    expect(res.body).toEqual([{ name: 'nginx' }]);
  });

  it('GET /api/services handles error', async () => {
    vi.spyOn(SystemStats, 'getServices').mockRejectedValue(new Error('fail'));
    const res = await request(app).get('/api/services?names=nginx');
    expect(res.status).toBe(500);
    expect(res.body).toHaveProperty('error');
  });
}); 