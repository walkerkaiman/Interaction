export interface ModuleConfig {
  [key: string]: any;
}

export abstract class BaseModule {
  protected config: ModuleConfig;
  protected manifest: any;
  protected log: (msg: string, level?: string) => void;
  private locked: boolean = false;

  constructor(config: ModuleConfig, manifest: any, log: (msg: string, level?: string) => void) {
    this.config = config;
    this.manifest = manifest;
    this.log = log;
  }

  lock() {
    this.locked = true;
    this.log('Module locked', 'System');
  }

  unlock() {
    this.locked = false;
    this.log('Module unlocked', 'System');
  }

  setConfig(newConfig: ModuleConfig) {
    this.config = newConfig;
    this.log('Module config updated', 'System');
  }

  isLocked() {
    return this.locked;
  }

  async start(): Promise<void> {
    try {
      await this.onStart();
    } catch (err) {
      this.log(`Error in start: ${err}`, 'Error');
    }
  }

  async stop(): Promise<void> {
    try {
      await this.onStop();
    } catch (err) {
      this.log(`Error in stop: ${err}`, 'Error');
    }
  }

  handleEvent(event: any): void {
    try {
      this.onHandleEvent(event);
    } catch (err) {
      this.log(`Error in handleEvent: ${err}`, 'Error');
    }
  }

  // Abstract methods to be implemented by subclasses
  protected abstract onStart(): void | Promise<void>;
  protected abstract onStop(): void | Promise<void>;
  protected abstract onHandleEvent(event: any): void;
  protected emitEvent(event: any): void {
    // To be implemented by the system
  }
  public getModuleName(): string {
    return this.manifest?.name || '';
  }
} 