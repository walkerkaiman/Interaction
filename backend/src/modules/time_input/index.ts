import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
import manifest from '../../../../shared/manifests/time_input.json';

export class TimeInputModule extends InputModuleBase {
  static manifest = manifest;
  private countdownInterval: NodeJS.Timeout | null = null;
  private lastCountdown: string = '';
  private isRunningState: boolean = false;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
    // Start countdown immediately when module is instantiated
    this.isRunningState = true;
    this.startCountdown();
  }

  async start(): Promise<void> { 
    this.log('TimeInputModule started', 'Time');
    this.isRunningState = true;
    this.startCountdown();
  }

  async stop(): Promise<void> { 
    this.log('TimeInputModule stopped', 'Time');
    this.isRunningState = false;
    this.stopCountdown();
  }

  protected async onStart(): Promise<void> {
    this.isRunningState = true;
    this.startCountdown();
  }

  protected async onStop(): Promise<void> {
    this.isRunningState = false;
    this.stopCountdown();
  }

  protected async onHandleEvent(event: any): Promise<void> {}

  protected onGetTriggerParameters(): any { 
    return { countdown: this.getCountdown() };
  }

  private startCountdown(): void {
    this.stopCountdown(); // Clear any existing interval
    this.countdownInterval = setInterval(() => {
      const countdown = this.getCountdown();
      if (countdown !== this.lastCountdown) {
        this.lastCountdown = countdown;
        // Emit countdown update
        this.emitEvent({ type: 'countdown_update', countdown });
      }
    }, 1000); // Update every second
  }

  private stopCountdown(): void {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
  }

  private getCountdown(): string {
    const targetTime = this.config.target_time;
    if (!targetTime) return 'No target time set';

    try {
      const now = new Date();
      const timeParts = targetTime.split(':').map(Number);
      // If any part is NaN, treat as invalid
      if (timeParts.some(isNaN)) {
        throw new Error('Invalid time format');
      }
      // Handle both HH:MM and HH:MM:SS formats
      const hours = timeParts[0] || 0;
      const minutes = timeParts[1] || 0;
      const seconds = timeParts[2] || 0;
      // Create target time for today
      const target = new Date();
      target.setHours(hours, minutes, seconds, 0);
      // If target time has passed today, set it for tomorrow
      if (target <= now) {
        target.setDate(target.getDate() + 1);
      }
      const diff = target.getTime() - now.getTime();
      const totalSeconds = Math.floor(diff / 1000);
      if (totalSeconds <= 0) {
        this.log(`[System] Countdown reached zero, emitting trigger event`, 'System');
        this.onTrigger({ type: 'trigger', source: this.getModuleName(), timestamp: now.toISOString() });
        return 'Time to trigger!';
      }
      // If the countdown is exactly 24h 0m 0s, treat as trigger (for midnight edge case)
      if (totalSeconds === 24 * 3600) {
        this.log(`[System] Countdown reached zero (midnight edge), emitting trigger event`, 'System');
        this.onTrigger({ type: 'trigger', source: this.getModuleName(), timestamp: now.toISOString() });
        return 'Time to trigger!';
      }
      const hoursLeft = Math.floor(totalSeconds / 3600);
      const minutesLeft = Math.floor((totalSeconds % 3600) / 60);
      const secondsLeft = totalSeconds % 60;
      const result = hoursLeft > 0 
        ? `${hoursLeft}h ${minutesLeft}m ${secondsLeft}s`
        : minutesLeft > 0 
          ? `${minutesLeft}m ${secondsLeft}s`
          : `${secondsLeft}s`;
      // Debug logging
      this.log(`Countdown for ${targetTime}: ${result} (target: ${target.toISOString()}, now: ${now.toISOString()})`, 'Time');
      return result;
    } catch (error) {
      this.log(`Error calculating countdown for ${targetTime}: ${error}`, 'Error');
      return 'Invalid time format';
    }
  }

  // Public method to check if module is running
  isRunning(): boolean {
    return this.isRunningState;
  }

  // Public method to get countdown for API
  getCountdownInfo(): { countdown: string; target_time: string; isActive: boolean } {
    return {
      countdown: this.getCountdown(),
      target_time: this.config.target_time || '',
      isActive: this.isRunningState
    };
  }

  onTrigger(event: any) {
    this.log(`[System] TimeInputModule trigger: ${JSON.stringify(event)}`, 'System');
    try {
      this.emitEvent(event);
    } catch (err) {
      this.log(`[System] Error in onTrigger: ${err}`, 'Error');
    }
  }

  onStream(value: any) {
    this.log(`TimeInputModule stream: ${JSON.stringify(value)}`, 'Time');
    this.emitEvent({ value });
  }
} 