import { useState, useEffect, useRef } from "react";
import { startLab, stopLab, getLabTypes, getActiveSession } from "./api";
import type { LabSession, LabType } from "./api";

// Utility function to extract error message from unknown error types
function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "An unexpected error occurred";
}

// Dashboard component is the main UI for managing lab sessions, 
// allowing users to select a lab type, start/stop sessions, and view session status. 
// It uses React hooks for state management and side effects, 
// and calls the API client functions to interact with the backend.
export default function Dashboard() {
  const [labTypes, setLabTypes] = useState<LabType[]>([]);
  const [selectedLabTypeId, setSelectedLabTypeId] = useState<number | null>(null);
  const [session, setSession] = useState<LabSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const canStart = !loading && selectedLabTypeId !== null && labTypes.length > 0;

  // Load lab types and any active session from the backend when the component mounts
  useEffect(() => {
    getLabTypes()
      .then((types) => {
        setLabTypes(types);
        if (types.length > 0) setSelectedLabTypeId(types[0].id);
      })
      .catch(() => setError("Failed to load lab types"));

    getActiveSession()
      .then((s) => { if (s) setSession(s); })  // Set the active session if it exists
      .catch(() => setError("Failed to fetch active session"));
  }, []);

  // Countdown timer: ticks every second while session is running with an expiration_time
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);

    if (session?.status === "running" && session.expiration_time) {
      const expiry = new Date(session.expiration_time).getTime();

      const tick = () => {
        const remaining = Math.max(0, expiry - Date.now());
        if (remaining === 0) {
          setTimeLeft("Expired");
          setSession((prev) => prev ? { ...prev, status: "expired" } : prev);
          clearInterval(timerRef.current!);
          return;
        }
        const mins = Math.floor(remaining / 60000);
        const secs = Math.floor((remaining % 60000) / 1000);
        setTimeLeft(`${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`);
      };

      tick();
      timerRef.current = setInterval(tick, 1000);
    } else {
      setTimeLeft(null);
    }

    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [session?.status, session?.expiration_time]);

  async function handleStart() {
    if (session && session.status === "running") {
      setError("Please stop your current lab before starting a new one.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      if (selectedLabTypeId === null) return;
      const s = await startLab(selectedLabTypeId);
      setSession(s);
    } catch (error: unknown) {
      setError(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function handleStop() {
    if (!session) return;
    setError(null);
    setLoading(true);
    try {
      await stopLab(session.id);
      setSession((prev) => prev ? { ...prev, status: "stopped" } : prev); // copies all existing session fields and just overrides status
    } catch (error: unknown) {
      setError(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1 style={{ textAlign: "center" }}>KubeRange Dashboard</h1>

      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, justifyContent: "center" }}>
          <label htmlFor="lab-select">Lab Type:</label>
          <select
            id="lab-select"
            value={selectedLabTypeId ?? undefined}
            onChange={(e) => setSelectedLabTypeId(Number(e.target.value))}
            disabled={loading}
          >
            {labTypes.map((lab) => (
              <option key={lab.id} value={lab.id}>
                {lab.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginTop: 16, display: "flex", gap: 8, justifyContent: "center" }}>
          <button onClick={handleStart} disabled={!canStart}>
            Start
          </button>
          <button onClick={handleStop} disabled={loading || !session}>
            Stop
          </button>
        </div>
      </div>

      {error && (
        <p style={{ color: "red", marginTop: 16 }}>{error}</p>
      )}

      {session && (
        <div style={{ marginTop: 24, padding: "8px 16px 16px", border: "1px solid #ccc", borderRadius: 6 }}>
          <h2 style={{ textAlign: "center", marginTop: 8, marginBottom: 24 }}>Session Status</h2>
          <table>
            <tbody>
              <tr><td><b>Session ID</b></td><td>{session.id}</td></tr>
              <tr><td><b>Status</b></td><td>{session.status}</td></tr>
              <tr><td><b>Pod Name</b></td><td>{session.pod_name ?? "—"}</td></tr>
              <tr><td><b>URL</b></td><td>{session.url ? <a href={session.url} target="_blank" rel="noreferrer">{session.url}</a> : "—"}</td></tr>
              <tr><td><b>Start Time</b></td><td>{session.start_time ?? "—"}</td></tr>
              <tr><td><b>Expiration Time</b></td><td>{session.expiration_time ?? "—"}</td></tr>
              {timeLeft !== null && (
                <tr><td><b>Expires In</b></td><td>{timeLeft}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
