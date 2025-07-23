import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
import manifest from '../../../../shared/manifests/frames_input.json';

export class FramesInputModule extends InputModuleBase {
  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }
  async start(): Promise<void> { this.log('FramesInputModule started', 'Frames'); }
  async stop(): Promise<void> { this.log('FramesInputModule stopped', 'Frames'); }
  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}
  protected onGetTriggerParameters(): any { return {}; }
  onTrigger(event: any) { this.log(`FramesInputModule trigger: ${JSON.stringify(event)}`, 'verbose'); }
  onStream(value: any) { this.log(`FramesInputModule stream: ${JSON.stringify(value)}`, 'verbose'); }
} 