import fs from 'fs';
import path from 'path';
import { BaseModule, ModuleConfig } from './BaseModule';
import { Logger } from './Logger';

export class ModuleLoader {
  private logger: Logger;
  private moduleRegistry: Record<string, any>;

  constructor(logger: Logger, moduleRegistry?: Record<string, any>) {
    this.logger = logger;
    this.moduleRegistry = moduleRegistry || {};
  }

  static buildRegistryFromFilesystem(): Record<string, any> {
    const modulesDir = path.join(__dirname, '../modules');
    const registry: Record<string, any> = {};
    fs.readdirSync(modulesDir, { withFileTypes: true }).forEach(dirent => {
      if (dirent.isDirectory()) {
        const moduleName = dirent.name;
        if (moduleName === 'module_base') return;
        try {
          // Load the compiled JS file
          const mod = require(path.join(modulesDir, moduleName, 'index.js'));
          // Find the exported class (assume it's the only class exported)
          const exportedClass = Object.values(mod).find(v => typeof v === 'function');
          if (exportedClass) {
            registry[moduleName] = exportedClass;
            console.log(`[System] Loaded module: ${moduleName}`);
          }
        } catch (err) {
          console.error(`[System] Failed to load module ${moduleName}:`, err);
        }
      }
    });
    return registry;
  }

  getModuleClass(name: string) {
    return this.moduleRegistry[name];
  }

  loadModulesFromConfig(configPath: string): BaseModule[] {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    const modules: BaseModule[] = [];
    if (config.interactions) {
      for (const interaction of config.interactions) {
        // Input
        const inputModName = interaction.input.module;
        const inputConfig = interaction.input.config;
        const InputClass = this.moduleRegistry[inputModName];
        if (InputClass) {
          modules.push(new InputClass(inputConfig, this.logger.log.bind(this.logger)));
          this.logger.log(`[System] Loaded input module: ${inputModName} with config: ${JSON.stringify(inputConfig)}`, 'System');
        } else {
          this.logger.log(`[System] Unknown input module: ${inputModName}`, 'System');
        }
        // Output
        const outputModName = interaction.output.module;
        const outputConfig = interaction.output.config;
        const OutputClass = this.moduleRegistry[outputModName];
        if (OutputClass) {
          modules.push(new OutputClass(outputConfig, this.logger.log.bind(this.logger)));
          this.logger.log(`[System] Loaded output module: ${outputModName} with config: ${JSON.stringify(outputConfig)}`, 'System');
        } else {
          this.logger.log(`[System] Unknown output module: ${outputModName}`, 'System');
        }
      }
    }
    return modules;
  }

  getAvailableModules() {
    // Return metadata for all modules
    const availableModules = Object.entries(this.moduleRegistry).map(([key, ModuleClass]) => {
      let manifest = {};
      try {
        manifest = ModuleClass.prototype.manifest || ModuleClass.manifest || {};
      } catch {
        // fallback if manifest is not accessible
      }
      return {
        name: key,
        manifest,
      };
    });
    console.log(`[System] Returning ${availableModules.length} available modules.`);
    return availableModules;
  }
} 