# Interaction Project Structure

## Overview
This is a modular interaction framework with a Node.js/TypeScript backend and React frontend.

## Project Structure
```
Interaction/
├── backend/                 # Backend server (Node.js/TypeScript)
│   ├── src/                # TypeScript source files
│   │   ├── index.ts        # Main server file
│   │   └── core/           # Core modules
│   ├── dist/               # Compiled JavaScript (auto-generated)
│   ├── package.json        # Backend dependencies
│   └── tsconfig.json       # TypeScript configuration
├── web-frontend/           # React frontend
│   ├── src/                # React source files
│   ├── dist/               # Built frontend (auto-generated)
│   └── package.json        # Frontend dependencies
├── config/                 # Configuration files
├── loading.html            # Loading screen
└── start_interaction.bat   # Main startup script
```

## How to Run

### Option 1: Use the batch file (Recommended)
```bash
start_interaction.bat
```
This will:
1. Install dependencies for both backend and frontend
2. Build both projects
3. Open the loading screen
4. Start the backend server

### Option 2: Manual startup
```bash
# Backend
cd backend
npm install
npm run build
npm start

# Frontend (in another terminal)
cd web-frontend
npm install
npm run build
```

## Important Notes

### File Locations
- **Main server file**: `backend/src/index.ts` (NOT `backend/index.ts`)
- **TypeScript config**: `backend/tsconfig.json` (compiles `src/` to `dist/`)
- **Frontend build**: `web-frontend/dist/` (served by backend)

### Dependencies
- Backend dependencies are in `backend/package.json`
- Frontend dependencies are in `web-frontend/package.json`
- **No root-level package.json needed**

### Ports
- Backend server: `http://localhost:8000`
- Loading screen: Opens `loading.html` locally
- Main app: `http://localhost:8000/` (served by backend)

## Troubleshooting

### Server not starting
1. Check that `backend/src/index.ts` exists
2. Run `cd backend && npm run build` to recompile
3. Check for TypeScript errors
4. Ensure all dependencies are installed: `cd backend && npm install`
5. Check for missing runtime dependencies (like multer)

### API endpoints not working
1. Ensure backend is running on port 8000
2. Check that API routes are defined in `backend/src/index.ts`
3. Verify CORS headers are set

### Loading screen issues
1. Ensure `loading.html` is in the project root
2. Check that backend `/api/status` endpoint responds
3. Verify browser can access `http://localhost:8000` 