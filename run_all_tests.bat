@echo off
REM Run all backend and frontend tests

echo Running backend tests...
npm run test:backend

echo Running frontend tests...
npm run test:frontend

echo All tests completed. 