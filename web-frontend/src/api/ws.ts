import { io, Socket } from 'socket.io-client';

const WS_URL = 'ws://localhost:8000/ws/events'; // Updated to match backend

let socket: WebSocket | null = null;
let messageHandlers: ((data: any) => void)[] = [];

export function connectWebSocket() {
  if (!socket) {
    socket = new WebSocket('ws://localhost:8000/ws/events');

    socket.onopen = () => {
      // console.log('WebSocket connected');
    };

    socket.onclose = () => {
      // console.log('WebSocket disconnected');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // console.log('Received event:', data);
        // console.log('Number of message handlers:', messageHandlers.length);
        // Call all registered message handlers
        messageHandlers.forEach((handler, index) => {
          try {
            // console.log(`Calling handler ${index}:`, handler);
            handler(data);
          } catch (e) {
            console.error('Error in message handler:', e);
          }
        });
      } catch (e) {
        // console.log('Received non-JSON message:', event.data);
      }
    };
  }
  return socket;
}

export function addMessageHandler(handler: (data: any) => void) {
  messageHandlers.push(handler);
}

export function removeMessageHandler(handler: (data: any) => void) {
  const index = messageHandlers.indexOf(handler);
  if (index > -1) {
    messageHandlers.splice(index, 1);
  }
}

export function getSocket(): WebSocket | null {
  return socket;
}

export default connectWebSocket; 