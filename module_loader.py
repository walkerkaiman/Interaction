import os
import importlib.util
import json

MODULES_PATH = os.path.join(os.path.dirname(__file__), "modules")


class ModuleLoader:
    def __init__(self):
        self.module_registry = {}  # module_name: { manifest, class_ref }

    def discover_modules(self, log_callback=print):
        for folder in os.listdir(MODULES_PATH):
            folder_path = os.path.join(MODULES_PATH, folder)
            if not os.path.isdir(folder_path):
                continue
            if folder == "module_base":
                continue

            manifest_path = os.path.join(folder_path, "manifest.json")
            if not os.path.exists(manifest_path):
                continue

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)

                entry_file = manifest.get("entry_point")
                class_name = manifest.get("class_name")
                if not entry_file or not class_name:
                    continue

                entry_path = os.path.join(folder_path, entry_file)
                class_ref = self._import_class(entry_path, class_name)

                self.module_registry[folder] = {
                    "manifest": manifest,
                    "class_ref": class_ref,
                    "folder": folder
                }
                log_callback(f"✅ Registered module: '{folder}' as '{manifest.get('name', 'Unnamed')}'")

            except Exception as e:
                log_callback(f"⚠️ Failed to load module '{folder}': {e}")

    def _import_class(self, filepath, class_name):
        spec = importlib.util.spec_from_file_location(class_name, filepath)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {filepath}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    def get_available_modules(self):
        """Returns a list of (module_name, manifest) tuples."""
        return [
            (name, data["manifest"])
            for name, data in self.module_registry.items()
        ]

    def create_instance(self, module_name, config, log_callback=print):
        """Creates a new instance of a module with config and optional logging."""
        if module_name not in self.module_registry:
            available = list(self.module_registry.keys())
            error_msg = (
                f"❌ Module '{module_name}' not found in registry.\n"
                f"📂 Available modules: {available}\n"
                f"🧪 Check that:\n"
                f"  - The folder name is '{module_name}'\n"
                f"  - 'manifest.json' exists inside it\n"
                f"  - 'entry_point' and 'class_name' in the manifest are correct\n"
            )
            raise Exception(error_msg)

        entry = self.module_registry[module_name]
        module_class = entry.get("class_ref")
        manifest = entry.get("manifest")

        if not module_class:
            raise Exception(f"⚠️ No class_ref found for module '{module_name}'. Possible import error.")

        return module_class(config=config, manifest=manifest, log_callback=log_callback)

