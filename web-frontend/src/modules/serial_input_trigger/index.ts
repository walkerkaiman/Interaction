// @ts-nocheck
import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
// @ts-ignore
import manifest from './manifest.json';
const SerialPort = require('serialport');

export class SerialInputModule extends InputModuleBase {
  config: any;
  log: (msg: string, level?: string) => void;
  private serialPort: any = null;
  private parser: any = null;
  private connectionStatus: string = 'disconnected';
  private currentValue: number | null = null;
  private triggerStatus: boolean = false;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
    this.config = config;
    this.log = log;
    this.initSerial();
  }

  initSerial() {
    if (this.serialPort) {
      this.serialPort.close();
      this.serialPort = null;
    }
    this.connectionStatus = 'disconnected';
    if (!this.config.port) return;
    this.serialPort = new SerialPort(this.config.port, { baudRate: this.config.baud_rate || 9600 });
    this.parser = this.serialPort.pipe(new SerialPort.parsers.Readline({ delimiter: '\n' }));
    this.serialPort.on('open', () => {
      this.connectionStatus = 'connected';
      this.log('Serial port opened: ' + this.config.port, 'serial');
    });
    this.serialPort.on('close', () => {
      this.connectionStatus = 'disconnected';
      this.log('Serial port closed: ' + this.config.port, 'serial');
    });
    this.serialPort.on('error', (err: any) => {
      this.connectionStatus = 'error';
      this.log('Serial port error: ' + err, 'serial');
    });
    this.parser.on('data', (data: string) => {
      const value = parseFloat(data.trim());
      if (isNaN(value)) return;
      this.currentValue = value;
      if (this.mode === 'trigger') {
        if (this.checkTrigger(value)) {
          if (!this.triggerStatus) {
            this.triggerStatus = true;
            this.onTrigger({ value });
          }
        } else {
          this.triggerStatus = false;
        }
      } else if (this.mode === 'streaming') {
        this.onStream(value);
      }
      this.log(`Serial data: ${value}`, 'serial');
    });
  }

  checkTrigger(value: number): boolean {
    const op = this.config.logic_operator || '>';
    const threshold = parseFloat(this.config.threshold_value ?? 0);
    if (op === '>') return value > threshold;
    if (op === '<') return value < threshold;
    if (op === '=') return value === threshold;
    return false;
  }

  start() {
    this.log('SerialInputModule started', 'outputs');
    this.initSerial();
  }

  stop() {
    this.log('SerialInputModule stopped', 'outputs');
    if (this.serialPort) {
      this.serialPort.close();
      this.serialPort = null;
    }
  }

  onTrigger(event: any) {
    this.log(`SerialInputModule trigger: ${JSON.stringify(event)}`, 'outputs');
    // Emit event to system (handled by base class or router)
  }

  onStream(value: any) {
    this.log(`SerialInputModule stream: ${JSON.stringify(value)}`, 'outputs');
    // Emit streaming value to system (handled by base class or router)
  }

  getTriggerParameters() {
    return {
      port: this.config.port,
      baud_rate: this.config.baud_rate,
      logic_operator: this.config.logic_operator,
      threshold_value: this.config.threshold_value,
    };
  }

  reset() {
    this.log('SerialInputModule reset', 'outputs');
    this.initSerial();
  }
} 