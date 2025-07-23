// @ts-ignore: wav-decoder has no types
import * as wav from 'wav-decoder';
import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
import manifest from './manifest.json';
import * as fs from 'fs';
import * as path from 'path';
import * as pureimage from 'pureimage';
// @ts-ignore: speaker has no types
import Speaker from 'speaker';

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
    const fullPath = path.join(__dirname, 'assets', 'audio', this.config.file_path);
    this.log('Playing audio file: ' + fullPath, 'Audio');
    this.playAudio(fullPath, this.getCurrentVolume());
  }

  setMasterVolume(vol: number) {
    this.masterVolume = Math.max(0, Math.min(100, vol));
    this.log(`Master volume set to ${this.masterVolume}`, 'Audio');
  }

  async playAudio(filePath: string, volume: number) {
    if (!filePath || !fs.existsSync(filePath)) {
      this.log('Audio file not found: ' + filePath, 'Audio');
      return;
    }
    try {
      const buffer = fs.readFileSync(filePath);
      const audioData = await wav.decode(buffer);
      const channelData = audioData.channelData;
      const numChannels = channelData.length;
      const sampleRate = audioData.sampleRate;
      const bitDepth = 16; // Speaker expects 16-bit PCM
      const length = channelData[0].length;
      // Prepare interleaved PCM buffer
      const pcmBuffer = Buffer.alloc(length * numChannels * 2); // 2 bytes per sample
      const vol = Math.max(0, Math.min(100, volume)) / 100;
      for (let i = 0; i < length; i++) {
        for (let ch = 0; ch < numChannels; ch++) {
          // Clamp and scale sample
          let sample = channelData[ch][i] * vol;
          sample = Math.max(-1, Math.min(1, sample));
          const intSample = Math.floor(sample * 32767);
          pcmBuffer.writeInt16LE(intSample, (i * numChannels + ch) * 2);
        }
      }
      const speaker = new Speaker({
        channels: numChannels,
        bitDepth,
        sampleRate,
      });
      speaker.on('error', (err: any) => {
        this.log('Speaker error: ' + err, 'Audio');
      });
      // Play the buffer (overlap supported)
      speaker.write(pcmBuffer);
      speaker.end();
      this.log('Audio playback started', 'Audio');
    } catch (err) {
      this.log('Audio playback error: ' + err, 'Audio');
    }
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