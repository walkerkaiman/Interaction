import { BaseModule, ModuleConfig } from './BaseModule';

export { ModuleConfig };

export abstract class OutputModuleBase extends BaseModule {
  protected currentMode: 'trigger' | 'streaming' = 'trigger';

  setMode(mode: 'trigger' | 'streaming') {
    try {
      this.currentMode = mode;
      this.log(`Output module mode set to ${mode}`, 'System');
    } catch (err) {
      this.log(`Error in setMode: ${err}`, 'Error');
    }
  }

  handleEvent(event: any) {
    try {
      if (event.mode === 'trigger') {
        this.log('Handling trigger event', 'System');
        this.onTriggerEvent(event);
      } else if (event.mode === 'streaming') {
        this.log('Handling streaming event', 'System');
        this.onStreamingEvent(event);
      }
    } catch (err) {
      this.log(`Error in handleEvent: ${err}`, 'Error');
    }
  }

  abstract onTriggerEvent(event: any): void;
  abstract onStreamingEvent(event: any): void;
} 