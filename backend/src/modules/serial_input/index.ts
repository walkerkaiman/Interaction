import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
import manifest from '../../../../shared/manifests/serial_input.json';

export class SerialInputModule extends InputModuleBase {
  static manifest = manifest;
  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }
  async start(): Promise<void> { this.log('SerialInputModule started', 'Serial'); }
  async stop(): Promise<void> { this.log('SerialInputModule stopped', 'Serial'); }
  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}
  protected onGetTriggerParameters(): any { return {}; }
  onTrigger(event: any) {
    this.log(`SerialInputModule trigger: ${JSON.stringify(event)}`, 'Serial');
    this.emitEvent(event);
  }
  onStream(value: any) {
    this.log(`SerialInputModule stream: ${JSON.stringify(value)}`, 'Serial');
    this.emitEvent({ value });
  }
} 