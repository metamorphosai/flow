export const FLOW_SPACE_WELCOME_SCRIPT = `[kind][peaceful] Hi.

[kind][peaceful] [calm] Welcome to Flow Space.

[kind][peaceful] You don’t need to do anything yet.

[kind][peaceful] This is a space to slow down.

[kind][peaceful] To come back to your breath.

[kind][peaceful] Over the next few days,

you’ll move through a simple rhythm.

Gently bringing your system back into balance.

There’s nothing to get right.

You can move at your own pace.

[peaceful] Repeat what feels good.

[kind][peaceful] Skip what doesn’t.

[kind][peaceful] [grounded] For now, just begin.

[kind][peaceful] [inviting] [slow] Start with Arrival.`;

export const FLOW_SPACE_WELCOME_FLAG = "flowSpaceWelcomePlayed";

export async function streamFlowSpaceAudio(text: string) {
  const res = await fetch("/api/elevenlabs/stream", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text, outputFormat: "mp3_22050_32" }),
  });

  if (!res.ok) throw new Error("Failed to stream welcome audio");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);

  return {
    play: () => audio.play(),
    cleanup: () => URL.revokeObjectURL(url),
  };
}

// Future sessions:
// - 00 Arrival script can be added here.
// - 01 Breath script can be added here.
