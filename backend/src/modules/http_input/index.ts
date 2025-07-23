import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
import manifest from '../../../../shared/manifests/http_input.json';
import express from 'express';
import bodyParser from 'body-parser';

export class HttpInputModule extends InputModuleBase {
  static manifest = manifest;
  private server: any = null;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }

  onGetTriggerParameters(): any {
    return { type: 'http_request' };
  }

  onTrigger(event: any): void {
    this.log('[HTTP Input] Trigger event received', 'System');
  }

  onStream(value: any): void {
    this.log('[HTTP Input] Stream event received', 'System');
  }

  async onStart(): Promise<void> {
    this.startServer();
  }

  async onStop(): Promise<void> {
    if (this.server) {
      this.server.close();
      this.log('[HTTP Input] Server stopped', 'outputs');
    }
  }

  onHandleEvent(event: any): void {
    this.log('[HTTP Input] Handling event', 'System');
  }

  startServer() {
    const { port, path: routePath, method, expected_body, response } = this.config;
    if (!port || !routePath) {
      this.log('HTTP Input: Port and path must be configured', 'Error');
      return;
    }
    const app = express();
    app.use(bodyParser.text({ type: '*/*' }));
    
    const httpMethod = method ? method.toLowerCase() : 'post';
    if (httpMethod === 'get') {
      app.get(routePath, (req: any, res: any) => this.handleRequest(req, res, expected_body, response));
    } else if (httpMethod === 'post') {
      app.post(routePath, (req: any, res: any) => this.handleRequest(req, res, expected_body, response));
    } else if (httpMethod === 'put') {
      app.put(routePath, (req: any, res: any) => this.handleRequest(req, res, expected_body, response));
    } else if (httpMethod === 'delete') {
      app.delete(routePath, (req: any, res: any) => this.handleRequest(req, res, expected_body, response));
    } else {
      app.post(routePath, (req: any, res: any) => this.handleRequest(req, res, expected_body, response));
    }
    
    this.server = app.listen(port, () => {
      this.log(`[HTTP Input] Listening on port ${port} path ${routePath}`, 'outputs');
    });
  }

  handleRequest(req: any, res: any, expected_body: string, response: string) {
    const reqBody = req.body;
    if (expected_body && reqBody !== expected_body) {
      this.log(`[HTTP Input] Received request with unexpected body: ${reqBody}`, 'outputs');
      res.status(400).send('Unexpected body');
      return;
    }
    this.log(`[HTTP Input] Received ${req.method} request on ${req.path} with body: ${reqBody}`, 'outputs');
    this.emitEvent({ body: reqBody, headers: req.headers, method: req.method, path: req.path });
    res.send(response || 'OK');
  }
} 