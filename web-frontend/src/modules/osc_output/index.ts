// @ts-nocheck
import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
// @ts-ignore
import manifest from './manifest.json';
const osc = require('osc');

export class OscOutputModule extends OutputModuleBase {
  private udpPort: any = null;
  config: any;
  log: (msg: string, level?: string) => void;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
    this.config = config;
    this.log = log;
    this.initOscPort();
  }

  initOscPort() {
    if (this.udpPort) {
      this.udpPort.close();
    }
    this.udpPort = new osc.UDPPort({
      localAddress: '0.0.0.0',
      localPort: 0, // OS assigns a random port
      remoteAddress: this.config.ip_address || '127.0.0.1',
      remotePort: this.config.port || 8000,
      metadata: true,
    });
    this.udpPort.open();
    this.udpPort.on('error', (err: any) => {
      this.log('OSC UDP error: ' + err, 'outputs');
    });
  }

  start() {
    this.log('OscOutputModule started', 'outputs');
    this.initOscPort();
  }

  stop() {
    this.log('OscOutputModule stopped', 'outputs');
    if (this.udpPort) {
      this.udpPort.close();
      this.udpPort = null;
    }
  }

  onTriggerEvent(event: any) {
    this.log(`OscOutputModule trigger event: ${JSON.stringify(event)}`, 'outputs');
    this.sendOscMessage(event.value ?? 1);
  }

  onStreamingEvent(event: any) {
    this.log(`OscOutputModule streaming event: ${JSON.stringify(event)}`, 'outputs');
    this.sendOscMessage(event.value ?? 0);
  }

  sendOscMessage(value: any) {
    if (!this.udpPort) this.initOscPort();
    const address = this.config.address || '/trigger';
    const msg = {
      address,
      args: Array.isArray(value) ? value : [value],
    };
    try {
      this.udpPort.send(msg);
      this.log(`OSC message sent to ${this.config.ip_address}:${this.config.port} ${address} ${JSON.stringify(msg.args)}`, 'osc');
    } catch (e) {
      this.log('OSC send error: ' + e, 'outputs');
    }
  }

  manualTrigger() {
    this.onTriggerEvent({ manual: true, value: 1 });
  }
} 