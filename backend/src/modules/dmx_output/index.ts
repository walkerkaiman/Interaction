import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
import manifest from '../../../../shared/manifests/dmx_output.json';

export class DmxOutputModule extends OutputModuleBase {
  static manifest = manifest;
  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }
  async start(): Promise<void> { this.log('DmxOutputModule started', 'DMX'); }
  async stop(): Promise<void> { this.log('DmxOutputModule stopped', 'DMX'); }
  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}
  onTriggerEvent(event: any) { this.log(`DmxOutputModule trigger event: ${JSON.stringify(event)}`, 'DMX'); }
  onStreamingEvent(event: any) { this.log(`DmxOutputModule streaming event: ${JSON.stringify(event)}`, 'DMX'); }
}