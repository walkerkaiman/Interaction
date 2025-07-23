const fs = require('fs');
const path = require('path');

const backendModulesDir = path.join(__dirname, '../backend/src/modules');
const frontendModulesDir = path.join(__dirname, '../frontend/src/modules');

function syncManifests() {
  const backendModules = fs.readdirSync(backendModulesDir, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  backendModules.forEach(moduleName => {
    const backendManifest = path.join(backendModulesDir, moduleName, 'manifest.json');
    const frontendModuleDir = path.join(frontendModulesDir, moduleName);
    const frontendManifest = path.join(frontendModuleDir, 'manifest.json');
    if (fs.existsSync(backendManifest)) {
      if (!fs.existsSync(frontendModuleDir)) {
        fs.mkdirSync(frontendModuleDir, { recursive: true });
        console.log(`Created frontend module directory: ${frontendModuleDir}`);
      }
      fs.copyFileSync(backendManifest, frontendManifest);
      console.log(`Synced manifest for module: ${moduleName}`);
    }
  });
}

syncManifests(); 