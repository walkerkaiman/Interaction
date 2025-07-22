import { BaseModule, ModuleConfig } from './BaseModule';
import { messageRouter } from './MessageRouter';

export { ModuleConfig };

export abstract class InputModuleBase extends BaseModule {
  protected mode: 'trigger' | 'streaming' = 'trigger';

  setMode(mode: 'trigger' | 'streaming') {
    try {
      this.mode = mode;
      this.log(`Input module mode set to ${mode}`, 'System');
    } catch (err) {
      this.log(`Error in setMode: ${err}`, 'Error');
    }
  }

  protected emitEvent(event: any) {
    try {
      messageRouter.routeEvent(this, event, this.mode);
    } catch (err) {
      this.log(`Error in emitEvent: ${err}`, 'Error');
    }
  }

  getTriggerParameters(): any {
    try {
      return this.onGetTriggerParameters();
    } catch (err) {
      this.log(`Error in getTriggerParameters: ${err}`, 'Error');
      return null;
    }
  }

  handleEvent(event: any) {
    try {
      if (this.mode === 'trigger') {
        this.log('Handling trigger event', 'System');
        this.onTrigger(event);
      } else if (this.mode === 'streaming') {
        this.log('Handling streaming event', 'System');
        this.onStream(event.value);
      }
    } catch (err) {
      this.log(`Error in handleEvent: ${err}`, 'Error');
    }
  }

  protected abstract onGetTriggerParameters(): any;
  abstract onTrigger(event: any): void;
  abstract onStream(value: any): void;
} 