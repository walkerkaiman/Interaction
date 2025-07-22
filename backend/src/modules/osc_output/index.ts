import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
import manifest from './manifest.json';

export class OscOutputModule extends OutputModuleBase {
  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }
  async start(): Promise<void> { this.log('OscOutputModule started', 'OSC'); }
  async stop(): Promise<void> { this.log('OscOutputModule stopped', 'OSC'); }
  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}
  onTriggerEvent(event: any) { this.log(`OscOutputModule trigger event: ${JSON.stringify(event)}`, 'OSC'); }
  onStreamingEvent(event: any) { this.log(`OscOutputModule streaming event: ${JSON.stringify(event)}`, 'OSC'); }
}