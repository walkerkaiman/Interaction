// @ts-ignore: wav-decoder has no types
import * as wav from 'wav-decoder';
import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
import manifest from './manifest.json';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';
import * as pureimage from 'pureimage';

const WAVEFORM_IMAGE_DIR = path.join(__dirname, 'assets', 'image');
if (!fs.existsSync(WAVEFORM_IMAGE_DIR)) {
  fs.mkdirSync(WAVEFORM_IMAGE_DIR, { recursive: true });
}

export class AudioOutputModule extends OutputModuleBase {
  static manifest = manifest;
  private masterVolume: number = 100;
  private waveformCache: Record<string, string> = {};

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
  }

  async start(): Promise<void> {
    this.log('AudioOutputModule started', 'Audio');
    if (this.config.file_path) {
      this.generateWaveform(this.config.file_path);
    }
  }

  async stop(): Promise<void> {
    this.log('AudioOutputModule stopped', 'Audio');
  }

  protected async onStart(): Promise<void> {}
  protected async onStop(): Promise<void> {}
  protected async onHandleEvent(event: any): Promise<void> {}

  onTriggerEvent(event: any) {
    this.log(`AudioOutputModule trigger event: ${JSON.stringify(event)}`, 'Audio');
    const fullPath = path.join(__dirname, 'assets', 'audio', this.config.file_path);
    this.playAudio(fullPath, this.getCurrentVolume());
  }

  onStreamingEvent(event: any) {
    this.log(`AudioOutputModule streaming event: ${JSON.stringify(event)}`, 'Audio');
    const fullPath = path.join(__dirname, 'assets', 'audio', this.config.file_path);
    this.playAudio(fullPath, this.getCurrentVolume());
  }

  manualTrigger() {
    this.log('Manual trigger received', 'Audio');
    // Resolve the full path to the audio file
    const fullPath = path.join(__dirname, 'assets', 'audio', this.config.file_path);
    this.log('Playing audio file: ' + fullPath, 'Audio');
    this.playAudio(fullPath, this.getCurrentVolume());
  }

  setMasterVolume(vol: number) {
    this.masterVolume = Math.max(0, Math.min(100, vol));
    this.log(`Master volume set to ${this.masterVolume}`, 'Audio');
  }

  playAudio(filePath: string, volume: number) {
    if (!filePath || !fs.existsSync(filePath)) {
      this.log('Audio file not found: ' + filePath, 'Audio');
      return;
    }
    // Use ffplay for playback with volume control
    const ffplay = spawn('ffplay', ['-nodisp', '-autoexit', '-volume', String(volume), filePath], {
      stdio: 'ignore',
      detached: true
    });
    ffplay.on('error', (err) => {
      this.log('ffplay error: ' + err, 'Audio');
    });
    ffplay.unref();
  }

  public async generateWaveform(filePath: string) {
    if (!filePath || !fs.existsSync(filePath)) {
      this.log('Audio file not found: ' + filePath, 'Audio');
      return;
    }
    const cacheFile = path.join(WAVEFORM_IMAGE_DIR, path.basename(filePath) + '.waveform.svg');
    if (fs.existsSync(cacheFile)) {
      this.waveformCache[filePath] = cacheFile;
      return cacheFile;
    }
    try {
      this.log('Generating SVG waveform for: ' + filePath, 'Audio');
      const buffer = fs.readFileSync(filePath);
      const audioData = await wav.decode(buffer);
      const channelData = audioData.channelData[0];
      const width = 400, height = 100;
      const samples = Math.min(400, channelData.length);
      const step = Math.floor(channelData.length / samples);
      let svgPath = '';
      for (let x = 0; x < samples; x++) {
        const idx = x * step;
        const sample = channelData[idx] || 0;
        const y = (1 - (sample + 1) / 2) * height;
        if (x === 0) {
          svgPath += `M ${x} ${y}`;
        } else {
          svgPath += ` L ${x} ${y}`;
        }
      }
      const svg = `<?xml version="1.0" encoding="UTF-8"?>\n<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">\n  <rect width="${width}" height="${height}" fill="black"/>\n  <path d="${svgPath}" stroke="lime" stroke-width="1" fill="none"/>\n</svg>`;
      fs.writeFileSync(cacheFile, svg);
      this.waveformCache[filePath] = cacheFile;
      this.log('SVG waveform generated successfully: ' + cacheFile, 'Audio');
      return cacheFile;
    } catch (err) {
      this.log('Waveform generation error: ' + err, 'Audio');
      console.error('Waveform generation failed:', err);
      throw err;
    }
  }

  getCurrentVolume(): number {
    // Prefer config.volume, fallback to masterVolume
    return typeof this.config.volume === 'number' ? this.config.volume : this.masterVolume;
  }
} 