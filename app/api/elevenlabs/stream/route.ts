import { NextRequest } from "next/server";

const ELEVENLABS_STREAM_URL = "https://api.elevenlabs.io/v1/text-to-speech";
const DEFAULT_OUTPUT_FORMAT = "mp3_22050_32";
const FALLBACK_OUTPUT_FORMAT = "mp3_44100_64";

export async function POST(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  const voiceId = process.env.ELEVENLABS_VOICE_ID;

  if (!apiKey || !voiceId) {
    return new Response(
      JSON.stringify({ error: "Missing ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID" }),
      { status: 500, headers: { "content-type": "application/json" } },
    );
  }

  const { text, outputFormat } = await req.json();

  if (!text || typeof text !== "string") {
    return new Response(JSON.stringify({ error: "text is required" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }

  const format = outputFormat || DEFAULT_OUTPUT_FORMAT;

  const makeRequest = async (selectedFormat: string) =>
    fetch(`${ELEVENLABS_STREAM_URL}/${voiceId}/stream`, {
      method: "POST",
      headers: {
        "xi-api-key": apiKey,
        "content-type": "application/json",
        accept: "audio/mpeg",
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_v3",
        output_format: selectedFormat,
      }),
    });

  let upstream = await makeRequest(format);

  // Fallback to heavier format when lightweight format is unavailable.
  if (!upstream.ok && format === DEFAULT_OUTPUT_FORMAT) {
    upstream = await makeRequest(FALLBACK_OUTPUT_FORMAT);
  }

  if (!upstream.ok || !upstream.body) {
    const errorText = await upstream.text();
    return new Response(
      JSON.stringify({ error: "ElevenLabs request failed", details: errorText }),
      { status: upstream.status || 502, headers: { "content-type": "application/json" } },
    );
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "content-type": "audio/mpeg",
      "cache-control": "no-store",
    },
  });
}
