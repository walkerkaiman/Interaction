let socket: WebSocket | null = null;
let messageHandlers: ((data: any) => void)[] = [];

export function connectWebSocket() {
  if (!socket) {
    const wsUrl = `ws://${window.location.hostname}:8000/`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      // Connection opened
    };

    socket.onclose = () => {
      // Connection closed
    };

    socket.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        messageHandlers.forEach((handler: (data: any) => void) => {
          try {
            handler(data);
          } catch (e) {
            console.error('Error in message handler:', e);
          }
        });
      } catch (e) {
        // Non-JSON message
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