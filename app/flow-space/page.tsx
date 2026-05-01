"use client";

import { useEffect, useState } from "react";
import {
  FLOW_SPACE_WELCOME_FLAG,
  FLOW_SPACE_WELCOME_SCRIPT,
  streamFlowSpaceAudio,
} from "@/lib/flowSpaceWelcome";

type Status = "idle" | "loading" | "playing" | "error" | "blocked";

export default function FlowSpacePage() {
  const [status, setStatus] = useState<Status>("idle");

  const playWelcome = async () => {
    try {
      setStatus("loading");
      const player = await streamFlowSpaceAudio(FLOW_SPACE_WELCOME_SCRIPT);
      await player.play();
      setStatus("playing");
      localStorage.setItem(FLOW_SPACE_WELCOME_FLAG, "true");
    } catch {
      // Browser autoplay policy often throws here.
      setStatus("blocked");
    }
  };

  useEffect(() => {
    // First-time users only.
    if (localStorage.getItem(FLOW_SPACE_WELCOME_FLAG) === "true") return;

    // Fire and forget so page render is never blocked.
    void playWelcome();
  }, []);

  return (
    <main>
      <h1>Flow Space</h1>
      {status === "loading" && <p>Loading welcome audio…</p>}
      {status === "error" && <p>Unable to load welcome audio right now.</p>}
      {status === "blocked" && (
        <button onClick={() => void playWelcome()}>Play welcome</button>
      )}
    </main>
  );
}
