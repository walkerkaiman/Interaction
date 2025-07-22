import fs from 'fs';
import path from 'path';
import { BaseModule, ModuleConfig } from './BaseModule';
import { Logger } from './Logger';

// Dynamically build the module registry
const modulesDir = path.join(__dirname, '../modules');
const moduleRegistry: Record<string, any> = {};

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
        moduleRegistry[moduleName] = exportedClass;
      }
    } catch (err) {
      console.error(`Failed to load module ${moduleName}:`, err);
    }
  }
});

export class ModuleLoader {
  private logger: Logger;
  constructor(logger: Logger) {
    this.logger = logger;
  }

  getModuleClass(name: string) {
    return moduleRegistry[name];
  }

  loadModulesFromConfig(configPath: string): BaseModule[] {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    const modules: BaseModule[] = [];
    if (config.interactions) {
      for (const interaction of config.interactions) {
        // Input
        const inputModName = interaction.input.module;
        const inputConfig = interaction.input.config;
        const InputClass = moduleRegistry[inputModName];
        if (InputClass) {
          modules.push(new InputClass(inputConfig, this.logger.log.bind(this.logger)));
        } else {
          this.logger.log(`Unknown input module: ${inputModName}`, 'System');
        }
        // Output
        const outputModName = interaction.output.module;
        const outputConfig = interaction.output.config;
        const OutputClass = moduleRegistry[outputModName];
        if (OutputClass) {
          modules.push(new OutputClass(outputConfig, this.logger.log.bind(this.logger)));
        } else {
          this.logger.log(`Unknown output module: ${outputModName}`, 'System');
        }
      }
    }
    return modules;
  }

  getAvailableModules() {
    // Return metadata for all modules
    return Object.entries(moduleRegistry).map(([key, ModuleClass]) => {
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
  }
} 