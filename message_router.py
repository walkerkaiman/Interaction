import os
import json
from module_loader import ModuleLoader


CONFIG_PATH = os.path.join("config", "interactions", "interactions.json")


class MessageRouter:
    def __init__(self, log_callback=print):
        self.loader = ModuleLoader()
        self.loader.discover_modules()
        self.log = log_callback

        self.routes = []  # list of {input, output}
        self.running_modules = []  # all module instances (to stop later)

    def load_interactions(self):
    if not os.path.exists(CONFIG_PATH):
        self.log("⚠️ No interaction config found.")
        return

    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)

    for interaction in data.get("interactions", []):
        input_cfg = interaction.get("input")
        output_cfg = interaction.get("output")
        if not input_cfg or not output_cfg:
            self.log("⚠️ Skipping invalid interaction.")
            continue

        input_module = self.loader.create_instance(
            input_cfg["module"],
            input_cfg["config"],
            log_callback=self.log
        )
        output_module = self.loader.create_instance(
            output_cfg["module"],
            output_cfg["config"],
            log_callback=self.log
        )

        def make_callback(output):
            def handler(data=None):
                self.log(f"📤 Event triggered → {output_cfg['module']}")
                output.handle_event(data)
            return handler

        if hasattr(input_module, "set_event_callback"):
            input_module.set_event_callback(make_callback(output_module))
        else:
            self.log(f"⚠️ {input_cfg['module']} does not support event callbacks")

        self.routes.append({
            "input": input_module,
            "output": output_module
        })

        self.running_modules.extend([input_module, output_module])

    def start_all(self):
        for route in self.routes:
            route["input"].start()
            route["output"].start()

    def stop_all(self):
        for module in self.running_modules:
            module.stop()
