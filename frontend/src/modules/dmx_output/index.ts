// @ts-nocheck
import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
// @ts-ignore
import manifest from '../../../../shared/manifests/dmx_output.json';
const sacn = require('sacn');
const artnet = require('artnet');
const SerialPort = require('serialport');
const parse = require('csv-parse/lib/sync');
import fs from 'fs';

export class DmxOutputModule extends OutputModuleBase {
  config: any;
  log: (msg: string, level?: string) => void;
  private dmxClient: any = null;
  private serialPort: any = null;
  private frames: number[][] = [];
  private chaseInterval: any = null;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
    this.config = config;
    this.log = log;
    this.initProtocol();
    if (this.config.csv_file) {
      this.loadFrames(this.config.csv_file);
    }
  }

  initProtocol() {
    if (this.config.protocol === 'sACN') {
      this.dmxClient = new sacn.Sender({ universe: this.config.universe || 1 });
      this.dmxClient.send(Buffer.alloc(512));
    } else if (this.config.protocol === 'Art-Net') {
      this.dmxClient = artnet({
        host: this.config.ip_address || '127.0.0.1',
        port: this.config.port || 6454,
        net: this.config.net || 0,
        subnet: this.config.subnet || 0,
        universe: this.config.universe || 0,
      });
    } else if (this.config.protocol === 'Serial DMX') {
      this.serialPort = new SerialPort(this.config.serial_port, { baudRate: 250000 });
      this.serialPort.on('error', (err: any) => this.log('Serial DMX error: ' + err, 'outputs'));
    }
  }

  loadFrames(csvPath: string) {
    try {
      const csv = fs.readFileSync(csvPath, 'utf-8');
      const records = parse(csv, { skip_empty_lines: true });
      this.frames = records.map((row: string[]) => row.map(v => parseInt(v, 10)));
      this.log(`Loaded ${this.frames.length} DMX frames from CSV`, 'outputs');
    } catch (e) {
      this.log('CSV parse error: ' + e, 'outputs');
    }
  }

  start() {
    this.log('DmxOutputModule started', 'outputs');
    this.initProtocol();
  }

  stop() {
    this.log('DmxOutputModule stopped', 'outputs');
    if (this.chaseInterval) clearInterval(this.chaseInterval);
    if (this.dmxClient && this.dmxClient.close) this.dmxClient.close();
    if (this.serialPort) this.serialPort.close();
  }

  onTriggerEvent(event: any) {
    this.log(`DmxOutputModule trigger event: ${JSON.stringify(event)}`, 'outputs');
    if (this.frames.length > 0) {
      this.playChase();
    }
  }

  onStreamingEvent(event: any) {
    this.log(`DmxOutputModule streaming event: ${JSON.stringify(event)}`, 'outputs');
    // Map event.value to DMX channels (assume array of 512 values)
    const dmxData = Array.isArray(event.value) ? event.value : [event.value];
    this.sendDmxFrame(dmxData);
  }

  playChase() {
    if (this.chaseInterval) clearInterval(this.chaseInterval);
    let frameIdx = 0;
    const fps = this.config.fps || 10;
    this.chaseInterval = setInterval(() => {
      if (frameIdx >= this.frames.length) {
        clearInterval(this.chaseInterval);
        return;
      }
      this.sendDmxFrame(this.frames[frameIdx]);
      frameIdx++;
    }, 1000 / fps);
  }

  sendDmxFrame(frame: number[]) {
    if (this.config.protocol === 'sACN' && this.dmxClient) {
      this.dmxClient.send(Buffer.from(frame));
    } else if (this.config.protocol === 'Art-Net' && this.dmxClient) {
      this.dmxClient.set(frame);
    } else if (this.config.protocol === 'Serial DMX' && this.serialPort) {
      this.serialPort.write(Buffer.from(frame));
    }
    this.log(`DMX frame sent: ${frame.slice(0, 8).join(',')}...`, 'outputs');
  }

  manualTrigger() {
    this.onTriggerEvent({ manual: true });
  }
} 