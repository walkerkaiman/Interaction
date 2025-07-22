import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
import manifest from './manifest.json';

export class OscInputModule extends InputModuleBase {
  static manifest = manifest;
  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }
  async start(): Promise<void> { this.log('OscInputModule started', 'OSC'); }
  async stop(): Promise<void> { this.log('OscInputModule stopped', 'OSC'); }
  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}
  protected onGetTriggerParameters(): any { return {}; }
  onTrigger(event: any) {
    this.log(`OscInputModule trigger: ${JSON.stringify(event)}`, 'OSC');
    this.emitEvent(event);
  }
  onStream(value: any) {
    this.log(`OscInputModule stream: ${JSON.stringify(value)}`, 'OSC');
    this.emitEvent({ value });
  }
} 