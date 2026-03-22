import { useEffect } from "react";
import { useChatStore } from "../stores/chatStore";
import type { HardwareStats } from "../types";

const API_URL = "http://127.0.0.1:8420/api/hardware";
const POLL_INTERVAL = 2000;

export function useHardware() {
  const setHardwareStats = useChatStore((s) => s.setHardwareStats);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const res = await fetch(API_URL);
        if (res.ok && active) {
          const stats: HardwareStats = await res.json();
          setHardwareStats(stats);
        }
      } catch {
        // Backend not available — ignore
      }
    };

    poll();
    const id = setInterval(poll, POLL_INTERVAL);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [setHardwareStats]);
}
