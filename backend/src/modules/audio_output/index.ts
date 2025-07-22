// @ts-ignore: wav-decoder has no types
import * as wav from 'wav-decoder';
import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
import manifest from './manifest.json';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';
import * as pureimage from 'pureimage';

const WAVEFORM_CACHE_DIR = path.join(__dirname, 'waveform_cache');
if (!fs.existsSync(WAVEFORM_CACHE_DIR)) fs.mkdirSync(WAVEFORM_CACHE_DIR);

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
    this.playAudio(this.config.file_path, this.getCurrentVolume());
  }

  onStreamingEvent(event: any) {
    this.log(`AudioOutputModule streaming event: ${JSON.stringify(event)}`, 'Audio');
    this.playAudio(this.config.file_path, this.getCurrentVolume());
  }

  manualTrigger() {
    this.log('Manual trigger received', 'Audio');
    this.playAudio(this.config.file_path, this.getCurrentVolume());
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

  async generateWaveform(filePath: string) {
    if (!filePath || !fs.existsSync(filePath)) return;
    const cacheFile = path.join(WAVEFORM_CACHE_DIR, path.basename(filePath) + '.waveform.png');
    if (fs.existsSync(cacheFile)) {
      this.waveformCache[filePath] = cacheFile;
      return cacheFile;
    }
    try {
      const buffer = fs.readFileSync(filePath);
      const audioData = await wav.decode(buffer);
      const channelData = audioData.channelData[0];
      const width = 400, height = 100;
      const img = pureimage.make(width, height, {});
      const ctx = img.getContext('2d');
      ctx.fillStyle = 'black';
      ctx.fillRect(0, 0, width, height);
      ctx.strokeStyle = 'lime';
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const idx = Math.floor((x / width) * channelData.length);
        const y = (1 - (channelData[idx] + 1) / 2) * height;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      await pureimage.encodePNGToStream(img, fs.createWriteStream(cacheFile));
      this.waveformCache[filePath] = cacheFile;
      this.log('Waveform generated: ' + cacheFile, 'Audio');
      return cacheFile;
    } catch (err) {
      this.log('Waveform generation error: ' + err, 'Audio');
    }
  }

  getCurrentVolume(): number {
    // Prefer config.volume, fallback to masterVolume
    return typeof this.config.volume === 'number' ? this.config.volume : this.masterVolume;
  }
} 