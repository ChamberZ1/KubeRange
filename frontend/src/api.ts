// api.ts - API client for interacting with the backend Lab Session Manager, 
// tells the frontend how to call the backend endpoints and what data to expect back
// In K8s, nginx proxies /api/* to the backend service.
// In local dev, vite proxies /api/* to localhost:8000 (see vite.config.ts).
const BASE_URL = "/api";

export interface LabType {
  id: number;
  name: string;
  image: string;
  port: number;
  description: string | null;  // description can be null if not provided by the backend (this matches the LabTypeResponse from the backend which has description as optional)
}

// Return an array of LabType objects as the backend returns an array
export async function getLabTypes(): Promise<LabType[]> { 
  const res = await fetch(`${BASE_URL}/lab-types`);  // Call the backend endpoint to get lab types
  if (!res.ok) throw new Error(`Failed to fetch lab types: ${res.status}`);
  return res.json();
}

// Define TypeScript interfaces mirroring LabSessionResponse from the backend
export interface LabSession {
  id: number;
  lab_type_id: number;
  pod_name: string | null;
  url: string | null;
  status: string;
  start_time: string | null;
  expiration_time: string | null;
}

// Call the backend endpoint to start a lab session with the selected lab type ID, return the LabSession object as the backend returns it
export async function startLab(labTypeId: number): Promise<LabSession> {  
  const res = await fetch(`${BASE_URL}/start/${labTypeId}`, { method: "POST" });  
  if (!res.ok) {
    const body = await res.json();
    throw new Error(body.detail || `Failed to start lab: ${res.status}`);
  }
  return res.json();
}

// Call the backend endpoint to get the currently running session, or null if none exists
export async function getActiveSession(): Promise<LabSession | null> {
  const res = await fetch(`${BASE_URL}/session/active`);
  if (!res.ok) throw new Error(`Failed to fetch active session: ${res.status}`);
  return res.json();
}

// Call the backend endpoint to stop a lab session with the given session ID, return a message and the session ID for confirmation
export async function stopLab(sessionId: number): Promise<{ message: string; session_id: number }> {
  const res = await fetch(`${BASE_URL}/stop/${sessionId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to stop lab: ${res.status}`);
  return res.json();
}
