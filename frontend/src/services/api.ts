/**
 * API client for the FastAPI backend.
 *
 * This is the ONLY place in the frontend that talks to the server. Components
 * call these typed functions instead of using axios/fetch directly, so if an
 * endpoint changes you only need to update this file.
 *
 * All business logic (prompts, AI provider fallback, parsing, exports) lives in
 * the Python `core` package - the frontend only sends inputs and renders results.
 *
 * In development, Vite proxies `/api/*` to the backend (see vite.config.ts).
 * In production, FastAPI serves this app, so relative URLs just work.
 */
import axios, { AxiosError } from "axios";

// ---------------------------------------------------------------------------
// HTTP client & error handling
// ---------------------------------------------------------------------------

const http = axios.create({ baseURL: "/api" });

/** Error shape returned by every backend endpoint. */
interface ApiErrorBody {
  error: string;
  code: string;
  details?: unknown;
}

/** Error thrown by every function in this module. */
export class ApiError extends Error {
  constructor(
    message: string,
    /** HTTP status code (0 when the server could not be reached). */
    public readonly status: number,
    /** Stable machine-readable code from the backend, e.g. "invalid_ai_response". */
    public readonly code: string,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** True when the backend reported a rate limit / quota error. */
export function isRateLimitError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 429;
}

function toApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const body = error.response?.data as Partial<ApiErrorBody> | undefined;
    return new ApiError(
      body?.error || error.message,
      error.response?.status ?? 0,
      body?.code || "network_error",
      body?.details,
    );
  }
  return new ApiError(error instanceof Error ? error.message : String(error), 0, "unknown_error");
}

async function get<T>(url: string): Promise<T> {
  try {
    const res = await http.get<T>(url);
    return res.data;
  } catch (error) {
    throw toApiError(error);
  }
}

async function post<T>(url: string, body: unknown): Promise<T> {
  try {
    const res = await http.post<T>(url, body);
    return res.data;
  } catch (error) {
    throw toApiError(error);
  }
}

// ---------------------------------------------------------------------------
// AI selection (popup before Step 1)
// ---------------------------------------------------------------------------

/** Text AI the user can pick: a cloud AI or any local Ollama model. No fallback. */
export type AIProvider = "gemini" | "openai" | "groq" | `ollama:${string}`;

/** Voice-over AI the user can pick (UnrealSpeech is cloud, the rest run locally). */
export type VoiceProvider = "unrealspeech" | "kokoro" | "piper" | "xtts" | "melo" | "bark";

/** Image AI the user can pick. The backend uses only that one (no fallback). */
export type ImageProvider = "openai" | "leonardo" | "gemini" | "sd15" | "sdxl-turbo" | "sdxl" | "flux-schnell";

/** Local image-to-video model. */
export type VideoProvider = "ltx-video" | "svd-xt" | "wan-1.3b" | "cogvideox-2b";

/** Tool that renders the final video. */
export type CompileProvider = "ffmpeg" | "moviepy" | "kdenlive";

/** Tasks the user picks an AI for. */
export type AITaskId = "topics" | "script" | "voice" | "image" | "video" | "compile";

/** One AI option and whether it can be used right now. */
export interface ProviderStatus {
  id: string;
  label: string;
  available: boolean;
  /** Why it can't be used (e.g. missing API key, model not downloaded). */
  reason: string | null;
  /** Runs on this machine (no API key, no internet). */
  local: boolean;
  /** Short tip about speed / quality. */
  note: string | null;
}

/** A task with its AI options. */
export interface AITaskOptions {
  id: AITaskId;
  label: string;
  /** Not implemented yet - shown but can't be picked. */
  comingSoon: boolean;
  options: ProviderStatus[];
}

/** Every task with its AI options (availability = API key set / local model ready). */
export async function fetchAIOptions(): Promise<AITaskOptions[]> {
  const res = await get<{ tasks: AITaskOptions[] }>("/ai-options");
  return res.tasks;
}

/** Check that a provider actually works (API key accepted / local model running). */
export async function verifyAIProvider(provider: string): Promise<ProviderStatus> {
  return post<ProviderStatus>("/ai-options/verify", { provider });
}

// ---------------------------------------------------------------------------
// Step 2 - Topics
// ---------------------------------------------------------------------------

/** 10 evergreen topic ideas for a niche. */
export async function fetchBasicTopics(niche: string, duration: string, provider?: AIProvider): Promise<string[]> {
  const data = await post<{ topics: string[] }>("/topics/basic", { niche, duration, provider });
  return data.topics;
}

/** 10 creative, viral-style topic ideas. */
export async function fetchUniqueTopics(niche: string, provider?: AIProvider): Promise<string[]> {
  const data = await post<{ topics: string[] }>("/topics/unique", { niche, provider });
  return data.topics;
}

/** 10 topic ideas based on live news + Google Trends (research happens server-side). */
export async function fetchTrendingTopics(niche: string, provider?: AIProvider): Promise<string[]> {
  const data = await post<{ topics: string[] }>("/topics/trending", { niche, provider });
  return data.topics;
}

// ---------------------------------------------------------------------------
// Step 3 - Script
// ---------------------------------------------------------------------------

export interface ScriptParams {
  topic: string;
  niche: string;
  duration: string;
  style: string;
  provider?: AIProvider;
}

/** Generate the voice-over script for a topic. */
export async function generateScript(params: ScriptParams): Promise<string> {
  const data = await post<{ script: string }>("/script", params);
  return data.script;
}

/** Short "narrative strategy" summary of a script. */
export async function summarizeScript(script: string, provider?: AIProvider): Promise<string> {
  const data = await post<{ summary: string }>("/script/summary", { script, provider });
  return data.summary;
}

export type ExportFormat = "txt" | "docx";

/** Render the script as a downloadable file (built by the backend). */
export async function exportScript(topic: string, script: string, format: ExportFormat): Promise<Blob> {
  try {
    const res = await http.post<Blob>("/script/export", { topic, script, format }, { responseType: "blob" });
    return res.data;
  } catch (error) {
    throw toApiError(error);
  }
}

// ---------------------------------------------------------------------------
// Step 4 - Audio
// ---------------------------------------------------------------------------

export interface TTSParams {
  text: string;
  voice: string;
  speed: number;
  pitch: number;
  provider: VoiceProvider;
}

/** A voice offered by a voice-over AI. */
export interface Voice {
  id: string;
  name: string;
  desc: string;
  type: string;
}

/** Voices of a voice-over AI. */
export async function fetchVoices(provider: VoiceProvider): Promise<Voice[]> {
  const data = await get<{ voices: Voice[] }>(`/tts/voices?provider=${encodeURIComponent(provider)}`);
  return data.voices;
}

/** Narrate the script. Returns the URL of the generated audio (MP3 or WAV). */
export async function generateSpeech(params: TTSParams): Promise<string> {
  const data = await post<{ OutputUri?: string }>("/tts", params);
  if (!data.OutputUri) throw new ApiError("No URL returned from API", 200, "invalid_response");
  return data.OutputUri;
}

// ---------------------------------------------------------------------------
// Step 5 - Scenes & images
// ---------------------------------------------------------------------------

/** Split the script into `sceneCount` scene texts (with the user's script AI). */
export async function splitScriptIntoScenes(script: string, sceneCount: number, provider?: AIProvider): Promise<string[]> {
  const data = await post<{ scenes: string[] }>("/scenes/split", { script, sceneCount, provider });
  return data.scenes;
}

/** Generate a detailed image prompt for one scene (with the user's script AI). */
export async function generateScenePrompt(text: string, style: string, provider?: AIProvider): Promise<string> {
  const data = await post<{ prompt: string }>("/scenes/prompt", { text, style, provider });
  return data.prompt;
}

/** Generate an image for a prompt. Returns an image URL (http or data: URI). */
export async function generateImage(prompt: string, provider?: ImageProvider): Promise<string> {
  const data = await post<{ url: string }>("/generate-image", { prompt, provider });
  return data.url;
}

// ---------------------------------------------------------------------------
// Steps 6-7 - Video
// ---------------------------------------------------------------------------

/** Animate a scene image into a video clip with a local model. Returns the clip URL. */
export async function generateSceneVideo(imageUrl: string, prompt: string, provider: VideoProvider): Promise<string> {
  const data = await post<{ url: string }>("/generate-video", { imageUrl, prompt, provider });
  return data.url;
}

/** Stitch all scene clips + narration into the final video. Returns its URL. */
export async function compileVideo(
  scenes: { id: number; videoUrl?: string | null; text?: string }[],
  audioUrl: string,
  provider: CompileProvider,
): Promise<string> {
  // Only what the renderer needs (scenes also carry large data: URI images).
  const payload = scenes.map(({ id, videoUrl, text }) => ({ id, videoUrl, text }));
  const data = await post<{ url: string }>("/compile-video", { scenes: payload, audioUrl, provider });
  return data.url;
}

// ---------------------------------------------------------------------------
// Step 8 - Download
// ---------------------------------------------------------------------------

/** Upper bound for building the ZIP (the backend downloads every media file). */
const EXPORT_TIMEOUT_MS = 5 * 60 * 1000;

/** Everything produced by the pipeline, sent to the backend to build the ZIP. */
export interface ProjectExport {
  niche: string;
  style: string;
  duration: string;
  aspectRatio: string;
  sceneCount: number;
  topic: string;
  script: string;
  summary: string;
  audioUrl: string;
  finalVideoUrl: string;
  scenes: { text: string; prompt?: string; selectedImage?: string | null; videoUrl?: string | null }[];
}

/**
 * Build the project ZIP: project_details.xlsx, script.txt, images/img1..N,
 * videos/vid1..N, audio/narration and final_video (see core/services/project_export.py).
 */
export async function downloadProjectPackage(project: ProjectExport): Promise<Blob> {
  try {
    const res = await http.post<Blob>("/export/project", project, {
      responseType: "blob",
      // Never leave the button stuck on "Packaging..." if the connection drops.
      timeout: EXPORT_TIMEOUT_MS,
    });
    return res.data;
  } catch (error) {
    throw toApiError(error);
  }
}
