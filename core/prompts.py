"""
Prompt templates.

Most of the app's "intelligence" lives here. Tweak these functions to change
the tone, structure or quality of generated content. Each function returns a
plain string that is sent to the LLM as the user prompt.
"""

from __future__ import annotations

from textwrap import dedent


def _clean(text: str) -> str:
    """Remove the indentation that comes from writing prompts inside functions."""
    return dedent(text).strip()


def topic_generator_basic(niche: str, duration: str, audience: str) -> str:
    """10 evergreen topic ideas for a niche."""
    return _clean(f"""
        Generate 10 viral YouTube topic ideas for the niche: "{niche}".
        The video duration is expected to be around {duration}.
        Target audience: "{audience}".
        Provide the response as a JSON array of strings. Output ONLY the JSON.
    """)


def topic_generator_unique(niche: str, context: str) -> str:
    """10 creative topic ideas that blend the niche with extra context (e.g. live trends)."""
    return _clean(f"""
        Generate 10 highly unique and trending YouTube topic ideas by combining the niche "{niche}" with this current context/trends: {context}.
        Focus on "hooky", viral-style concepts that stand out from the crowd.
        Provide the response as a JSON array of strings. Output ONLY the JSON.
    """)


def script_generator(topic: str, niche: str, duration: str, style: str) -> str:
    """Full voice-over script, clean enough to be fed directly into TTS."""
    return _clean(f"""
        Write a professional YouTube script for the topic: "{topic}".
        Niche: {niche}
        Target Duration: {duration}
        Style: {style}

        CRITICAL INSTRUCTIONS:
        1. Output ONLY the narrator's speech (voiceover text).
        2. DO NOT include speaker names like "Narrator:", "Host:", or "Visual:".
        3. DO NOT include any scene descriptions or stage directions in brackets [like this].
        4. DO NOT use any markdown formatting (no bold **, no italics *, no # headings).
        5. Provide the output as clean, plain text paragraphs that can be directly read by a text-to-speech engine.
    """)


def summary_generator(script: str) -> str:
    """Short summary (about a quarter of the script length)."""
    return _clean(f"""
        Provide a concise summary of the following YouTube script.
        The summary should be approximately 1/4th of the length of the original script.

        Script:
        {script}
    """)


def scene_prompt_generator(scene_text: str, style: str) -> str:
    """Detailed Midjourney-style image prompt for one scene."""
    return _clean(f"""
        Generate a HIGHLY DETAILED Midjourney v6 prompt based on this script segment: "{scene_text}".
        The overall production style is: {style}.

        Follow the Official Midjourney Prompting Structure:
        1. [Core Subject]: Detailed description of the main subject and their action.
        2. [Environment/Background]: Setting, atmosphere, lighting, time of day.
        3. [Technical details]: Camera lens (e.g. 35mm, 85mm), film stock (Kodak, Fujifilm), or rendering engine (Octane, Unreal).
        4. [Style]: Artistic influence or aesthetic (e.g. photorealistic, cinematic, minimalist).
        5. [Parameters]: ALWAYS include "--ar 16:9" at the end. Use "--v 6.1" and "--stylize 250" where appropriate.

        Format the output as a single cohesive paragraph followed by the parameters.
        Output ONLY the final prompt. NO explanations. NO preamble.
    """)


def one_liner_generator(scene_text: str) -> str:
    """Very short caption for a scene (currently unused by the UI, kept for future features)."""
    return _clean(f"""
        Provide a very short, one-liner caption (max 10 words) for the following scene.
        Scene: "{scene_text}"
    """)


def script_splitter(script: str, count: int) -> str:
    """Split a script into ``count`` scene segments, returned as a JSON array."""
    return _clean(f"""
        Split the following script into exactly {count} logical segments for video scenes.
        Each segment should be a self-contained part of the story.
        Do not break in the middle of a sentence.
        Provide the response as a JSON array of strings, where each string is a scene's text.

        Script:
        {script}
    """)
