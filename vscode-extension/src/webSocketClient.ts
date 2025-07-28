// src/websocketClient.ts
import { WebSocket, Data } from "ws";

export class xAICodeGeneratorClient {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5000;
  private isConnected = false;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pendingRequests = new Map<
    string,
    {
      resolve: (value: any) => void;
      reject: (reason: any) => void;
      timeout: NodeJS.Timeout;
    }
  >();

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Prevent duplicate connections
      if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
        reject(new Error("Already connecting"));
        return;
      }

      this.ws = new WebSocket("ws://localhost:8000/ws");

      this.ws.on("open", () => {
        console.log("Connected to backend");
        this.isConnected = true;
        this.clearReconnectTimer();
        resolve();
      });

      this.ws.on("error", (err) => {
        console.error("WebSocket error:", err);
        this.isConnected = false;
        reject(err);
      });

      this.ws.on("close", () => {
        console.log("Disconnected from backend");
        this.isConnected = false;
        this.rejectPendingRequests("Connection closed");
        this.scheduleReconnect();
      });

      this.ws.on("message", (data) => {
        this.handleMessage(data);
      });
    });
  }

  private handleMessage(data: Data) {
    try {
      const response = JSON.parse(data.toString());
      const requestId = response.requestId;

      const pending = this.pendingRequests.get(requestId);
      if (pending) {
        clearTimeout(pending.timeout);
        this.pendingRequests.delete(requestId);

        if (response.status === "success") {
          pending.resolve(response);
        } else {
          pending.reject(new Error(response.error || "Generation failed"));
        }
      }
    } catch (error) {
      console.error("Failed to parse message:", error);
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.isConnected) {
        console.log("Attempting to reconnect...");
        this.connect().catch((err) => {
          console.error("Reconnection failed:", err);
        });
      }
    }, this.reconnectInterval);
  }

  private clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private rejectPendingRequests(reason: string) {
    this.pendingRequests.forEach((pending) => {
      clearTimeout(pending.timeout);
      pending.reject(new Error(reason));
    });
    this.pendingRequests.clear();
  }

  async generateCode(task: string): Promise<any> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Not connected to backend");
    }

    const requestId = `${Date.now()}-${Math.random()}`;

    return new Promise((resolve, reject) => {
      // Set up timeout

      // Try to connect
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error("Request timeout after 30 seconds"));
      }, 300000);

      // Store pending request
      this.pendingRequests.set(requestId, { resolve, reject, timeout });

      // Send request
      const request = {
        command: "generate",
        task: task,
        requestId: requestId,
      };

      this.ws!.send(JSON.stringify(request));
    });
  }

  disconnect() {
    this.isConnected = false;
    this.clearReconnectTimer();
    this.rejectPendingRequests("Client disconnecting");

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
