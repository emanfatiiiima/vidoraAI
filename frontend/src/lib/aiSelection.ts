/**
 * The AIs the user picked in the popup before Step 1, and helpers the steps
 * share for reporting AI failures.
 *
 * Steps only read the selection; changing it always goes through the popup
 * (components/AISelectionModal.tsx), opened from the header or an error message.
 */
import {
  ApiError,
  isRateLimitError,
  type AIProvider,
  type CompileProvider,
  type ImageProvider,
  type VideoProvider,
  type VoiceProvider,
} from "../services/api";

/** One picked AI: the id sent to the backend and the label shown to the user. */
export interface AIChoice<T extends string = string> {
  id: T;
  label: string;
}

/** The AI used for each task of the project. */
export interface AISelection {
  topics: AIChoice<AIProvider>;
  /** Also used for scene splitting and image prompts (both are text work). */
  script: AIChoice<AIProvider>;
  voice: AIChoice<VoiceProvider>;
  image: AIChoice<ImageProvider>;
  video: AIChoice<VideoProvider>;
  compile: AIChoice<CompileProvider>;
}

/** Tasks that must have an AI before the project can start. */
export const REQUIRED_TASKS = ["topics", "script", "voice", "image", "video", "compile"] as const;

/** True when the error came from the AI itself (so picking another AI may help). */
export function isProviderError(error: unknown): boolean {
  return !(error instanceof ApiError && error.code === "network_error");
}

/**
 * A user-facing message for a failed AI call.
 *
 * @param action what the AI was doing, e.g. "generate topics".
 */
export function describeAIError(error: unknown, ai: AIChoice, action: string): string {
  if (!isProviderError(error)) return "Failed to reach the server. Please check your connection.";
  const extra = errorDetail(error);
  if (error instanceof ApiError && error.code === "provider_not_configured") {
    return `${ai.label} is not ready on the server.${extra}`;
  }
  if (error instanceof ApiError && error.code === "invalid_ai_response") {
    return `${ai.label} returned an invalid response.`;
  }
  if (error instanceof ApiError && error.code === "invalid_input") {
    return `${ai.label} couldn't ${action}: ${error.message}`;
  }
  if (isRateLimitError(error)) return `${ai.label} hit its quota limit.`;
  return `${ai.label} couldn't ${action}.${extra}`;
}

/** The backend's explanation (`details.hint` / `details.reason`), prefixed with a space. */
function errorDetail(error: unknown): string {
  if (!(error instanceof ApiError) || !error.details || typeof error.details !== "object") return "";
  const details = error.details as { hint?: unknown; reason?: unknown };
  const text = details.hint ?? details.reason;
  return typeof text === "string" && text ? ` ${text}` : "";
}
