import { io, Socket } from 'socket.io-client';

const WS_URL = 'ws://localhost:8000'; // Adjust as needed

let socket: Socket | null = null;

export function connectWebSocket() {
  if (!socket) {
    socket = io(WS_URL, {
      transports: ['websocket'],
    });

    socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    // Example: Listen for real-time events
    socket.on('event', (data) => {
      console.log('Received event:', data);
    });
  }
  return socket;
}

export function getSocket(): Socket | null {
  return socket;
}

export default connectWebSocket; 