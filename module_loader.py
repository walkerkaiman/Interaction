"""
Module Loader - Dynamic Module Discovery and Loading System

This file implements the dynamic module loading system for the Interaction framework.
The module loader is responsible for discovering, validating, and instantiating
modules at runtime without requiring code changes to the main application.

Key Responsibilities:
1. Scan the modules directory for available modules
2. Load and validate module manifests
3. Dynamically import module classes
4. Create module instances with proper configuration
5. Handle module loading errors gracefully

The module loader uses a plugin-like architecture where:
- Each module is a self-contained directory with a Python file and manifest
- Modules are discovered by scanning the modules directory
- Module metadata is defined in manifest.json files
- Module classes are dynamically imported and instantiated
- Configuration is validated against the module's schema

Author: Interaction Framework Team
License: MIT
"""

import os
import sys
import json
import importlib.util
from typing import Dict, List, Any, Optional, Type
from modules.module_base import ModuleBase

class InputEventRouter:
    """
    Shared event router for input modules. Allows multiple blocks to register for the same input config.
    When an input event is received, all matching blocks are triggered.
    """
    def __init__(self):
        # Map: (input_type, config_key_tuple) -> set of callbacks
        self.registry = {}

    def _make_key(self, input_type, config):
        """
        Create a hashable key for the input config. For OSC: (port, address).
        Extendable for other input types.
        """
        if input_type == "osc_input_trigger":
            port = int(config.get("port", 8000))
            address = config.get("address", "/trigger")
            return (input_type, port, address)
        # Add more input types here as needed
        # Fallback: use all config items as a tuple
        return (input_type, tuple(sorted(config.items())))

    def register(self, input_type, config, callback):
        key = self._make_key(input_type, config)
        if key not in self.registry:
            self.registry[key] = set()
        self.registry[key].add(callback)

    def unregister(self, input_type, config, callback):
        key = self._make_key(input_type, config)
        if key in self.registry and callback in self.registry[key]:
            self.registry[key].remove(callback)
            if not self.registry[key]:
                del self.registry[key]

    def dispatch_event(self, input_type, config, event):
        key = self._make_key(input_type, config)
        callbacks = self.registry.get(key, set())
        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                print(f"❌ Error in input event callback: {e}")

# Create a global instance for use by all modules/frontends
input_event_router = InputEventRouter()

class ModuleLoader:
    """
    Dynamic module discovery and loading system.
    
    The ModuleLoader is responsible for finding, validating, and creating
    instances of modules in the Interaction framework. It scans the modules
    directory for available modules and provides a unified interface for
    loading them with proper configuration.
    
    The loader uses a plugin-like architecture where each module is a
    self-contained directory containing:
    - A Python file with the module implementation
    - A manifest.json file with module metadata and configuration schema
    
    Key Features:
    - Automatic module discovery in the modules directory
    - Manifest validation and schema checking
    - Dynamic class loading and instantiation
    - Error handling and graceful degradation
    - Support for both input and output modules
    
    Attributes:
        modules_dir (str): Path to the modules directory
        available_modules (Dict): Cache of discovered modules
        loaded_modules (Dict): Cache of loaded module classes
    """
    
    def __init__(self, modules_dir: str = "modules"):
        """
        Initialize the module loader.
        
        Args:
            modules_dir (str): Path to the directory containing modules
            
        Note: The modules directory should contain subdirectories for each
        module, with each subdirectory containing a Python file and a
        manifest.json file.
        """
        self.modules_dir = modules_dir
        self.available_modules = {}
        self.loaded_modules = {}
        
        # Discover available modules on initialization
        self.discover_modules()
    
    def discover_modules(self):
        """
        Scan the modules directory and discover available modules.
        
        This method walks through the modules directory and finds all
        available modules by looking for directories that contain both
        a Python file and a manifest.json file.
        
        The discovered modules are cached in self.available_modules for
        quick access during module loading.
        
        Note: This method is called automatically during initialization
        and can be called again to refresh the module list if modules
        are added or removed while the application is running.
        """
        if not os.path.exists(self.modules_dir):
            print(f"⚠️ Modules directory '{self.modules_dir}' not found")
            return
        
        self.available_modules = {}
        
        # Walk through the modules directory
        for item in os.listdir(self.modules_dir):
            item_path = os.path.join(self.modules_dir, item)
            
            # Skip if not a directory
            if not os.path.isdir(item_path):
                continue
            
            # Skip the module_base directory (it's not a module)
            if item == "module_base" or item == "__pycache__":
                continue
            
            # Look for manifest.json and Python file
            manifest_path = os.path.join(item_path, "manifest.json")
            python_file = None
            
            # Find the Python file (should match the directory name)
            for file in os.listdir(item_path):
                if file.endswith('.py') and file != '__init__.py':
                    python_file = file
                    break
            
            if os.path.exists(manifest_path) and python_file:
                # This is a valid module directory
                module_name = item
                self.available_modules[module_name] = {
                    'path': item_path,
                    'manifest_path': manifest_path,
                    'python_file': python_file,
                    'manifest': None  # Will be loaded when needed
                }
                print(f"📦 Discovered module: {module_name}")
            else:
                print(f"⚠️ Invalid module directory: {item} (missing manifest.json or Python file)")
    
    def validate_manifest_fields(self, manifest):
        """
        Validate that every field in 'fields' has a corresponding entry in 'config_schema' and vice versa.
        Log a warning if there is a mismatch. If 'fields' is missing, auto-generate from 'config_schema'.
        """
        fields = manifest.get('fields')
        schema = manifest.get('config_schema')
        if schema and not fields:
            # Auto-generate fields from config_schema
            manifest['fields'] = [
                {
                    'name': k,
                    'type': v.get('type', 'text'),
                    'label': k.capitalize(),
                    'default': v.get('default', '')
                } for k, v in schema.items()
            ]
            print(f"⚠️ Auto-generated 'fields' from 'config_schema' for manifest: {manifest.get('name', 'unknown')}")
            return True
        if not fields and not schema:
            return False
        # If only fields exist without schema, that's valid
        if fields and not schema:
            return True
        # If only schema exists without fields, that's also valid (fields will be auto-generated)
        if schema and not fields:
            return True
        # Check for mismatches when both exist
        field_names = {f['name'] for f in fields}
        schema_names = set(schema.keys())
        missing_in_schema = field_names - schema_names
        missing_in_fields = schema_names - field_names
        if missing_in_schema:
            print(f"⚠️ Manifest field(s) missing in config_schema: {missing_in_schema}")
        if missing_in_fields:
            print(f"⚠️ config_schema key(s) missing in fields: {missing_in_fields}")
        return not (missing_in_schema or missing_in_fields)
    
    def load_manifest(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Load and validate a module's manifest file.
        
        Args:
            module_name (str): Name of the module to load manifest for
            
        Returns:
            Optional[Dict[str, Any]]: The loaded manifest, or None if loading failed
            
        Note: The manifest contains metadata about the module including its
        name, type (input/output), description, and configuration schema.
        This method validates that the manifest has the required fields.
        """
        if module_name not in self.available_modules:
            print(f"❌ Module '{module_name}' not found")
            return None
        
        module_info = self.available_modules[module_name]
        
        # Load manifest if not already loaded
        if module_info['manifest'] is None:
            try:
                with open(module_info['manifest_path'], 'r') as f:
                    manifest = json.load(f)
                
                # Validate required manifest fields
                required_fields = ['name', 'type', 'description']
                for field in required_fields:
                    if field not in manifest:
                        print(f"❌ Module '{module_name}' manifest missing required field: {field}")
                        return None
                
                # Validate module type
                if manifest['type'] not in ['input', 'output']:
                    print(f"❌ Module '{module_name}' has invalid type: {manifest['type']}")
                    return None
                
                # Validate classification if present
                if 'classification' in manifest:
                    if manifest['classification'] not in ['trigger', 'streaming']:
                        print(f"❌ Module '{module_name}' has invalid classification: {manifest['classification']}")
                        return None
                
                # Validate/cross-check fields and config_schema
                self.validate_manifest_fields(manifest)
                
                # Cache the manifest
                module_info['manifest'] = manifest
                
            except json.JSONDecodeError as e:
                print(f"❌ Module '{module_name}' has invalid manifest JSON: {e}")
                return None
            except Exception as e:
                print(f"❌ Error loading manifest for module '{module_name}': {e}")
                return None
        
        return module_info['manifest']
    
    def load_module_class(self, module_name: str) -> Optional[Type[ModuleBase]]:
        """
        Dynamically load a module's Python class.
        
        Args:
            module_name (str): Name of the module to load
            
        Returns:
            Optional[Type[ModuleBase]]: The loaded module class, or None if loading failed
            
        Note: This method uses Python's importlib to dynamically load the
        module's Python file and extract the module class. The class must
        inherit from ModuleBase and be the only class in the file (or be
        explicitly specified in the manifest).
        """
        if module_name not in self.available_modules:
            print(f"❌ Module '{module_name}' not found")
            return None
        
        # Return cached class if already loaded
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]
        
        module_info = self.available_modules[module_name]
        python_path = os.path.join(module_info['path'], module_info['python_file'])
        
        try:
            # Load the module using importlib
            spec = importlib.util.spec_from_file_location(module_name, python_path)
            if spec is None or spec.loader is None:
                print(f"❌ Could not load module spec for '{module_name}'")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the module class (should inherit from ModuleBase)
            module_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, ModuleBase) and 
                    attr != ModuleBase):
                    module_class = attr
                    break
            
            if module_class is None:
                print(f"❌ Module '{module_name}' does not contain a valid ModuleBase subclass")
                return None
            
            # Cache the loaded class
            self.loaded_modules[module_name] = module_class
            print(f"✅ Loaded module class: {module_name}")
            return module_class
            
        except Exception as e:
            print(f"❌ Error loading module class '{module_name}': {e}")
            return None
    
    def create_module_instance(self, module_name: str, config: Dict[str, Any], 
                              log_callback=print) -> Optional[ModuleBase]:
        """
        Create an instance of a module with the given configuration.
        
        Args:
            module_name (str): Name of the module to instantiate
            config (Dict[str, Any]): Configuration for the module instance
            log_callback: Function to call for logging (default: print)
            
        Returns:
            Optional[ModuleBase]: The created module instance, or None if creation failed
            
        Note: This method loads the module's manifest and class, validates
        the configuration against the manifest's schema, and creates an
        instance of the module with the provided configuration.
        """
        # Load manifest and validate configuration
        manifest = self.load_manifest(module_name)
        if manifest is None:
            return None
        
        # Validate configuration against manifest schema
        if not self._validate_config(config, manifest):
            return None
        
        # Load module class
        module_class = self.load_module_class(module_name)
        if module_class is None:
            return None
        
        try:
            # Create module instance
            instance = module_class(config, manifest, log_callback)
            print(f"✅ Created instance of module: {module_name}")
            return instance
            
        except Exception as e:
            print(f"❌ Error creating instance of module '{module_name}': {e}")
            return None
    
    def _validate_config(self, config: Dict[str, Any], manifest: Dict[str, Any]) -> bool:
        """
        Validate configuration against the module's manifest schema.
        
        Args:
            config (Dict[str, Any]): Configuration to validate
            manifest (Dict[str, Any]): Module manifest containing schema
            
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Note: This method checks that all required fields are present and
        that field types match the schema definition.
        """
        if 'config_schema' not in manifest and 'fields' not in manifest:
            return True  # No schema defined, assume valid
        
        schema = manifest['config_schema']
        
        # Check required fields
        for field_name, field_info in schema.items():
            if field_info.get('required', False) and field_name not in config:
                print(f"❌ Missing required configuration field: {field_name}")
                return False
            
            # Check field type if specified
            if field_name in config and 'type' in field_info:
                expected_type = field_info['type']
                actual_value = config[field_name]
                
                if expected_type == 'number' and not isinstance(actual_value, (int, float)):
                    print(f"❌ Configuration field '{field_name}' must be a number")
                    return False
                elif expected_type == 'string' and not isinstance(actual_value, str):
                    print(f"❌ Configuration field '{field_name}' must be a string")
                    return False
                elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                    print(f"❌ Configuration field '{field_name}' must be a boolean")
                    return False
        
        return True
    
    def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available modules.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of module information
            
        Note: This method returns information about all discovered modules,
        including their manifests. This is used by the GUI to display
        available modules and their configuration options.
        """
        modules_info = {}
        
        for module_name in self.available_modules:
            manifest = self.load_manifest(module_name)
            if manifest:
                modules_info[module_name] = {
                    'name': manifest.get('name', module_name),
                    'type': manifest.get('type', 'unknown'),
                    'classification': manifest.get('classification', 'unknown'),
                    'mode': manifest.get('mode', 'unknown'),
                    'description': manifest.get('description', ''),
                    'config_schema': manifest.get('config_schema', {}),
                    'path': self.available_modules[module_name]['path']
                }
        
        return modules_info
    
    def get_modules_by_type(self, module_type: str) -> List[str]:
        """
        Get a list of module names filtered by type.
        
        Args:
            module_type (str): Type of modules to return ('input' or 'output')
            
        Returns:
            List[str]: List of module names of the specified type
            
        Note: This method is useful for filtering modules by type when
        displaying them in the GUI (e.g., showing only input modules
        in the input dropdown).
        """
        modules = []
        
        for module_name in self.available_modules:
            manifest = self.load_manifest(module_name)
            if manifest and manifest.get('type') == module_type:
                modules.append(module_name)
        
        return modules
    
    def get_modules_by_classification(self, classification: str) -> List[str]:
        """
        Get a list of available modules of a specific classification.
        
        Args:
            classification (str): Classification of modules to return ('trigger' or 'streaming')
            
        Returns:
            List[str]: List of module names of the specified classification
        """
        modules = []
        
        for module_name in self.available_modules:
            manifest = self.load_manifest(module_name)
            if manifest and manifest.get('classification') == classification:
                modules.append(module_name)
        
        return modules
    
    def get_modules_by_type_and_classification(self, module_type: str, classification: str) -> List[str]:
        """
        Get a list of available modules of a specific type and classification.
        
        Args:
            module_type (str): Type of modules to return ('input' or 'output')
            classification (str): Classification of modules to return ('trigger' or 'streaming')
            
        Returns:
            List[str]: List of module names matching both criteria
        """
        modules = []
        
        for module_name in self.available_modules:
            manifest = self.load_manifest(module_name)
            if (manifest and 
                manifest.get('type') == module_type and 
                manifest.get('classification') == classification):
                modules.append(module_name)
        
        return modules
    
    def refresh_modules(self):
        """
        Refresh the module discovery cache.
        
        This method re-scans the modules directory and updates the
        available modules cache. It's useful when modules are added
        or removed while the application is running.
        
        Note: This method clears the loaded module cache and re-discovers
        all modules. It should be called when the module list needs to
        be updated.
        """
        self.available_modules = {}
        self.loaded_modules = {}
        self.discover_modules()
        print("🔄 Refreshed module discovery cache")

