# Interaction Framework

A modular, real-time framework for interactive art installations, built with **TypeScript (Node.js)** for the backend and **React** for the frontend. Easily connect sensors, triggers, and outputs (audio, DMX, OSC, etc.) with a modern web UI.

---

## Features

- **Modular architecture:** Plug-and-play input/output modules, each in its own folder with manifest and assets.
- **Dynamic module loader:** Only loads modules specified in config.
- **Real-time UI:** WebSocket-powered dashboard for live logs, performance, and configuration.
- **Performance monitoring:** Live CPU, memory, and temperature graphs.
- **Robust logging:** Filterable logs by level (System, Audio, OSC, Serial, DMX, etc.).
- **Easy configuration:** All settings in JSON, UI changes persist automatically.
- **Extensible:** Add new modules or UI pages with minimal boilerplate.

---

## Quick Start

### Prerequisites

- **Node.js** (v18+ recommended)
- **npm** (v9+)
- (Optional) **Python** (only for legacy modules/scripts)

### Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd Interaction
   ```

2. **Install dependencies:**
   ```sh
   # Backend
   cd backend
   npm install
   cd ..

   # Frontend
   cd frontend
   npm install
   cd ..
   ```

3. **Build and launch (recommended):**
   ```sh
   ./start_interaction.bat
   ```
   - This script installs, builds, and launches both backend and frontend, then opens the UI in your browser.

---

## Architecture

### Backend (Node.js/TypeScript)

- **Express server:** Serves API and static frontend.
- **WebSocket server:** Real-time updates for logs, performance, and module state.
- **Dynamic module loader:** Loads only modules listed in `config/interactions/interactions.json`.
- **Logging:** Centralized logger with multiple levels, broadcasts to frontend.
- **Performance monitoring:** Uses `systeminformation` for CPU, memory, temperature, etc.

### Frontend (React/TypeScript)

- **Material UI:** Modern, responsive design.
- **Zustand:** State management.
- **Vite:** Fast build and dev server.
- **Recharts:** Live graphs for performance.
- **Pages:** Module Wiki, Interactions, Console, Performance.

### Modules

- Each module lives in `backend/src/modules/<module>/`
- Contains:
  - `index.ts` (module logic)
  - `manifest.json` (metadata/config schema)
  - `assets/` (audio, images, etc.)
  - `wiki.md` (documentation, loaded in UI)

---

## Usage

### Web UI

- **Module Wiki:** Browse documentation for each module.
- **Interactions:** Create and configure input→output connections.
- **Console:** View and filter real-time logs.
- **Performance:** Live graphs for CPU, memory, temperature, and system info.

### Adding/Configuring Modules

- Add a new folder in `backend/src/modules/`
- Implement `index.ts` (extend InputModuleBase or OutputModuleBase)
- Add `manifest.json` and `wiki.md`
- Update `config/interactions/interactions.json` to include the new module

### Real-Time Monitoring

- All logs, state changes, and performance stats are pushed to the UI via WebSocket.
- UI and backend stay in sync automatically.

---

## Module Development

### Creating a New Module

1. **Create a new folder:**
   - `backend/src/modules/my_module/`
2. **Implement the module class:**
   - `index.ts` (extend `InputModuleBase` or `OutputModuleBase`)
   - Implement required methods: `start`, `stop`, `handleEvent`, etc.
3. **Add a manifest:**
   - `manifest.json` (describe config schema, metadata)
4. **Add documentation:**
   - `wiki.md` (markdown, loaded in UI)
5. **Add assets (if needed):**
   - `assets/` (audio, images, etc.)
6. **Register the module:**
   - Add to `config/interactions/interactions.json`

### Example Module Structure

```
backend/src/modules/my_module/
├── index.ts
├── manifest.json
├── wiki.md
└── assets/
```

### Manifest Example
```json
{
  "name": "my_module",
  "type": "input",
  "classification": "trigger",
  "description": "Custom input module for ...",
  "configSchema": {
    "param1": { "type": "string", "default": "foo" },
    "param2": { "type": "number", "default": 0 }
  }
}
```

---

## Configuration

- **Persistent config:** `config/interactions/interactions.json`
- **Module manifests:** `backend/src/modules/<module>/manifest.json`
- **Environment variables:** (optional) for ports, etc.

---

## API Reference

- `GET /modules` — List available modules
- `POST /modules/:id/settings` — Update module settings
- `POST /modules/:id/mode` — Change module mode (trigger/streaming)
- `GET /api/system_stats` (WebSocket) — Live performance data
- `GET /api/system_info` — Static system info
- `GET /api/processes` — Running processes
- `GET /api/log_levels` — Available log levels
- `GET /api/module_wiki/:module` — Module documentation

---

## Troubleshooting

- **UI not loading:** Make sure you’ve built the frontend (`npm run build` in `frontend`) and restarted the backend.
- **Port in use:** Change the port in backend or stop other services.
- **Logs not showing:** Ensure WebSocket is connected (check browser console).
- **Performance stats missing:** Check that `systeminformation` is installed in backend.
- **Module not loading:** Check for typos in `manifest.json` or missing required methods in `index.ts`.
- **Audio/DMX/OSC not working:** Ensure correct config and hardware is connected.

---

## Contributing

- Fork and clone the repo.
- Follow the modular structure for new modules.
- Add or update documentation in `wiki.md`.
- Use clear, descriptive commit messages.
- Open a pull request with your changes.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Credits

- [systeminformation](https://github.com/sebhildebrandt/systeminformation)
- [Material UI](https://mui.com/)
- [Recharts](https://recharts.org/)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [Vite](https://vitejs.dev/)
- And all contributors!

---

For detailed module documentation, see the Wiki section in the web UI.

## Shared Module Manifests

All module manifests are now stored in `shared/manifests/` at the project root. Both backend and frontend modules import their manifest from this shared directory. There are no longer `manifest.json` files in individual backend or frontend module folders.

To add or edit a module manifest, update the corresponding file in `shared/manifests/` (e.g., `shared/manifests/audio_output.json`).