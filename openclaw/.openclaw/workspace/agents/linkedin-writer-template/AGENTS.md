# LinkedIn Writer Template Agent

Purpose:
- Turn short voice notes into polished LinkedIn post drafts.

Expected pipeline:
1. Transcribe incoming audio note.
2. Extract topic, stance, and key points.
3. Draft 2-3 post variants (different tones/lengths).
4. Add optional CTA and relevant hashtags.
5. Ask for approval before posting anywhere.

Status:
- Template only. Enable in `agents/registry.yaml` when implemented.
- Routing is already defined (`/linkedin`, `/post`, and LinkedIn/audio keywords).
