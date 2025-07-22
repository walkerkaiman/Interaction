// @ts-nocheck
import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
// @ts-ignore
import manifest from './manifest.json';
const osc = require('osc');

export class OscInputModule extends InputModuleBase {
  config: any;
  log: (msg: string, level?: string) => void;
  private udpPort: any = null;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
    this.config = config;
    this.log = log;
    this.initOscListener();
  }

  initOscListener() {
    if (this.udpPort) {
      this.udpPort.close();
    }
    this.udpPort = new osc.UDPPort({
      localAddress: '0.0.0.0',
      localPort: this.config.port || 8000,
      metadata: true,
    });
    this.udpPort.on('message', (msg: any) => {
      if (msg.address === (this.config.address || '/trigger')) {
        if (this.mode === 'trigger') {
          this.onTrigger({ value: msg.args.length === 1 ? msg.args[0].value : msg.args.map((a: any) => a.value) });
        } else if (this.mode === 'streaming') {
          this.onStream(msg.args.length === 1 ? msg.args[0].value : msg.args.map((a: any) => a.value));
        }
        this.log(`OSC message received: ${msg.address} ${JSON.stringify(msg.args)}`, 'osc');
      }
    });
    this.udpPort.on('error', (err: any) => {
      this.log('OSC UDP error: ' + err, 'outputs');
    });
    this.udpPort.open();
  }

  start() {
    this.log('OscInputModule started', 'outputs');
    this.initOscListener();
  }

  stop() {
    this.log('OscInputModule stopped', 'outputs');
    if (this.udpPort) {
      this.udpPort.close();
      this.udpPort = null;
    }
  }

  onTrigger(event: any) {
    this.log(`OscInputModule trigger: ${JSON.stringify(event)}`, 'outputs');
    // Emit event to system (handled by base class or router)
  }

  onStream(value: any) {
    this.log(`OscInputModule stream: ${JSON.stringify(value)}`, 'outputs');
    // Emit streaming value to system (handled by base class or router)
  }

  getTriggerParameters() {
    return { port: this.config.port, address: this.config.address };
  }

  reset() {
    this.log('OscInputModule reset', 'outputs');
    this.initOscListener();
  }
} 