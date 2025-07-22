// @ts-nocheck
import { InputModuleBase, ModuleConfig } from '../../core/InputModuleBase';
// @ts-ignore
import manifest from './manifest.json';

export class TimeInputModule extends InputModuleBase {
  config: any;
  log: (msg: string, level?: string) => void;
  private timer: any = null;
  private lastTriggeredDate: string | null = null;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, { ...manifest, name: 'Time' }, log); // Show as 'Time' in dropdown
    this.config = config;
    this.log = log;
    this.startTimer();
  }

  startTimer() {
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => this.checkTime(), 1000);
  }

  checkTime() {
    const now = new Date();
    const currentTime = now.toTimeString().slice(0, 8);
    const targetTime = this.config.target_time || '12:00:00';
    const [h, m, s] = targetTime.split(':').map(Number);
    const target = new Date(now);
    target.setHours(h, m, s, 0);
    let countdown = (target.getTime() - now.getTime()) / 1000;
    if (countdown < 0) countdown += 24 * 3600; // Next day
    const countdownStr = new Date(countdown * 1000).toISOString().substr(11, 8);
    // Emit event with current time, countdown, and target time
    this.emitEvent({
      current_time: currentTime,
      countdown: countdownStr,
      target_time: targetTime,
      instance_id: this['instance_id'] || undefined,
    });
    // Trigger if countdown is zero (within 1 second)
    if (countdown < 1 && this.lastTriggeredDate !== now.toDateString()) {
      this.onTrigger({ current_time: currentTime, target_time: targetTime });
      this.lastTriggeredDate = now.toDateString();
    }
  }

  start() {
    this.log('TimeInputModule started', 'outputs');
    this.startTimer();
  }

  stop() {
    this.log('TimeInputModule stopped', 'outputs');
    if (this.timer) clearInterval(this.timer);
  }

  onTrigger(event: any) {
    this.log(`TimeInputModule trigger: ${JSON.stringify(event)}`, 'outputs');
    // Emit event to system (handled by base class or router)
  }

  onStream(value: any) {
    // Not used for time input
  }

  getTriggerParameters() {
    return { target_time: this.config.target_time };
  }
} 