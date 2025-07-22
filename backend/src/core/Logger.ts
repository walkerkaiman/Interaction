/**
 * Logger
 *
 * Supports log levels: Error, System, Audio, DMX, Frames, OSC, Serial, Time.
 * Broadcasts logs to the frontend via WebSocket.
 */

export type LogLevel = 'Error' | 'System' | 'Audio' | 'DMX' | 'Frames' | 'OSC' | 'Serial' | 'Time' | 'Performance';

export class Logger {
  private wsBroadcast?: (msg: any) => void;

  constructor(level: LogLevel = 'System', wsBroadcast?: (msg: any) => void) {
    this.wsBroadcast = wsBroadcast;
  }

  setBroadcast(fn: (msg: any) => void) {
    this.wsBroadcast = fn;
  }

  log(message: string, level: LogLevel = 'System') {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
    };
    // Print to server console
    // console.log(`[${level}]`, message);
    // Broadcast to frontend if available
    if (this.wsBroadcast) {
      this.wsBroadcast({ type: 'log', ...logEntry });
    }
  }

  logError(message: string) { this.log(message, 'Error'); }
  logSystem(message: string) { this.log(message, 'System'); }
  logAudio(message: string) { this.log(message, 'Audio'); }
  logDMX(message: string) { this.log(message, 'DMX'); }
  logFrames(message: string) { this.log(message, 'Frames'); }
  logOSC(message: string) { this.log(message, 'OSC'); }
  logSerial(message: string) { this.log(message, 'Serial'); }
  logTime(message: string) { this.log(message, 'Time'); }
} 