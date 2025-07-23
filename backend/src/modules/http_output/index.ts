import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
import manifest from '../../../../shared/manifests/http_output.json';

export class HttpOutputModule extends OutputModuleBase {
  static manifest = manifest;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }

  async onTriggerEvent(event: any) {
    await this.sendRequest('trigger');
  }

  async onStreamingEvent(event: any) {
    await this.sendRequest('streaming');
  }

  async onStart(): Promise<void> {
    this.log('[HTTP Output] Module started', 'System');
  }

  async onStop(): Promise<void> {
    this.log('[HTTP Output] Module stopped', 'System');
  }

  onHandleEvent(event: any): void {
    this.log('[HTTP Output] Handling event', 'System');
  }

  async manualTrigger() {
    await this.sendRequest('manual');
  }

  async sendRequest(source: string) {
    const { method, url, headers, body, timeout } = this.config;
    if (!url) {
      this.log('HTTP Output: No URL configured', 'Error');
      return;
    }
    try {
      const opts: any = {
        method: method || 'POST',
        headers: headers ? JSON.parse(headers) : {},
        body: ['POST', 'PUT', 'PATCH'].includes((method || '').toUpperCase()) ? body : undefined,
        timeout: timeout || 5000,
      };
      this.log(`[HTTP Output] Sending ${opts.method} to ${url} (source: ${source})`, 'outputs');
      
      // Use built-in fetch (Node.js 18+) or fallback to https module
      const res = await fetch(url, opts);
      const text = await res.text();
      this.log(`[HTTP Output] Response: ${res.status} ${res.statusText} - ${text}`, 'outputs');
    } catch (err: any) {
      this.log(`[HTTP Output] Error: ${err.message}`, 'Error');
    }
  }
} 