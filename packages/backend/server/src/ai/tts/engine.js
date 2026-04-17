// src/ai/tts/engine.js
import { Readable } from "stream";

const DEFAULT_PROVIDER = process.env.TTS_PROVIDER || "edge";

async function *edgeTTSStream(text, { voice = "en-US-AriaNeural", speed = 1.0 }) {
  const edge = await import("edge-tts");
  const tts = new edge.EdgeTTS({ voice, rate: speed });
  const audioStream = await tts.stream(text);
  for await (const chunk of audioStream) {
    yield new Uint8Array(chunk);
  }
}

async function *coquiTTSStream(text, { voice = "default", speed = 1.0 }) {
  const { TTS } = await import("coqui-tts");
  const modelPath = process.env.COQUI_MODEL || "tts_models/en/ljspeech/tacotron2-DDC";
  const tts = new TTS({ model_path: modelPath });
  const audioBuffer = await tts.tts(text, { speaker: voice, speed });
  const int16 = new Int16Array(audioBuffer.length);
  for (let i = 0; i < audioBuffer.length; i++) int16[i] = Math.max(-32768, Math.min(32767, audioBuffer[i] * 32767));
  yield new Uint8Array(int16.buffer);
}

async function *elevenLabsStream(text, { voice = "21m00Tcm4TlvDq8ikWAM", speed = 1.0 }) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) throw new Error("ELEVENLABS_API_KEY not set");
  const url = `https://api.elevenlabs.io/v1/text-to-speech/${voice}/stream`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "xi-api-key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, model_id: "eleven_monolingual_v1", voice_settings: { stability: 0.5, similarity_boost: 0.75, speed } })
  });
  if (!resp.ok) throw new Error(`ElevenLabs TTS error: ${resp.status}`);
  const reader = resp.body.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield new Uint8Array(value);
  }
}

async function *openaiStream(text, { voice = "alloy", speed = 1.0 }) {
  const { OpenAI } = await import("openai");
  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const resp = await client.audio.speech.create({
    model: "tts-1",
    voice,
    input: text,
    speed,
    response_format: "pcm"
  });
  const reader = resp.body.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield new Uint8Array(value);
  }
}

export async function* streamTTS(text, { voice = "default", speed = 1.0, provider = DEFAULT_PROVIDER } = {}) {
  try {
    switch (provider) {
      case "edge":
        yield* edgeTTSStream(text, { voice, speed });
        break;
      case "coqui":
        yield* coquiTTSStream(text, { voice, speed });
        break;
      case "eleven":
        yield* elevenLabsStream(text, { voice, speed });
        break;
      case "openai":
        yield* openaiStream(text, { voice, speed });
        break;
      default:
        console.warn(`[TTS] Unknown provider "${provider}", falling back to edge-tts`);
        yield* edgeTTSStream(text, { voice, speed });
    }
  } catch (err) {
    console.error("[TTS] Streaming failed:", err);
    throw err;
  }
}
