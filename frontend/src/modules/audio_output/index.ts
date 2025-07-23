// @ts-nocheck
import { OutputModuleBase, ModuleConfig } from '../../core/OutputModuleBase';
// @ts-ignore
import manifest from '../../../../shared/manifests/audio_output.json';
import path from 'path';
import fs from 'fs';
const player = require('play-sound')();
const wav = require('wav-decoder');
const { createCanvas } = require('canvas');

// In-memory cache for waveform images
const waveformCache: Record<string, Buffer> = {};
let masterVolume = 100; // Global master volume (0-100)

export class AudioOutputModule extends OutputModuleBase {
  private audioProcess: any = null;
  private waveformPath: string | null = null;
  config: any;
  log: (msg: string, level?: string) => void;

  constructor(config: ModuleConfig, log: (msg: string, level?: string) => void) {
    super(config, manifest, log);
    this.config = config;
    this.log = log;
  }

  start() {
    this.log('AudioOutputModule started', 'outputs');
    if (this.config.file_path) {
      this.generateWaveform(this.config.file_path);
    }
  }

  stop() {
    this.log('AudioOutputModule stopped', 'outputs');
    if (this.audioProcess) {
      this.audioProcess.kill();
      this.audioProcess = null;
    }
  }

  onTriggerEvent(event: any) {
    this.log(`AudioOutputModule trigger event: ${JSON.stringify(event)}`, 'outputs');
    if (this.config.file_path) {
      this.playAudio(this.config.file_path, this.config.volume ?? 100);
    }
  }

  onStreamingEvent(event: any) {
    this.onTriggerEvent(event);
  }

  playAudio(filePath: string, volume: number) {
    const effectiveVolume = Math.round((volume / 100) * (masterVolume / 100) * 100);
    this.audioProcess = player.play(filePath, (err: any) => {
      if (err) this.log('Audio playback error: ' + err, 'outputs');
    });
  }

  async generateWaveform(filePath: string) {
    const cacheKey = path.basename(filePath);
    if (waveformCache[cacheKey]) {
      this.waveformPath = cacheKey;
      return;
    }
    try {
      const buffer = fs.readFileSync(filePath);
      const audioData = await wav.decode(buffer);
      const width = 400, height = 100;
      const canvas = createCanvas(width, height);
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#222';
      ctx.fillRect(0, 0, width, height);
      ctx.strokeStyle = '#0ff';
      ctx.beginPath();
      const channel = audioData.channelData[0];
      for (let x = 0; x < width; x++) {
        const i = Math.floor((x / width) * channel.length);
        const y = (1 - (channel[i] + 1) / 2) * height;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      const out = canvas.toBuffer('image/png');
      waveformCache[cacheKey] = out;
      this.waveformPath = cacheKey;
    } catch (e) {
      this.log('Waveform generation error: ' + e, 'outputs');
    }
  }

  manualTrigger() {
    this.onTriggerEvent({ manual: true });
  }

  static setMasterVolume(vol: number) {
    masterVolume = Math.max(0, Math.min(100, vol));
  }
} 