import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
import manifest from '../../../../shared/manifests/time_input.json';

export class TimeInputModule extends InputModuleBase {
  static manifest = manifest;
  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }
  async start(): Promise<void> { this.log('TimeInputModule started', 'Time'); }
  async stop(): Promise<void> { this.log('TimeInputModule stopped', 'Time'); }
  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}
  protected onGetTriggerParameters(): any { return {}; }
  onTrigger(event: any) {
    this.log(`TimeInputModule trigger: ${JSON.stringify(event)}`, 'Time');
    this.emitEvent(event);
  }
  onStream(value: any) {
    this.log(`TimeInputModule stream: ${JSON.stringify(value)}`, 'Time');
    this.emitEvent({ value });
  }
} 