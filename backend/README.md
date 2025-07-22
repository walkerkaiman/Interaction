# Interaction Backend (Node.js/TypeScript)

## Setup

1. `cd backend`
2. `npm install`
3. `npm run build`
4. `npm start`

## Architecture
- Modular: Each module in `src/modules/` with its own manifest/config/assets
- Shared base class: `BaseModule` in `src/core/`
- Module loader: Loads and instantiates modules
- Message router: Routes events between modules
- Logger: Supports log levels (none, osc, serial, outputs, verbose)

See `src/modules/sample_module.ts` for a template module. 