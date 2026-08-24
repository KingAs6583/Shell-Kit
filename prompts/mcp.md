# Codebase Memory & CONTEXT.md Tracking Instructions

You are assisting with development on this codebase. To work efficiently, maintain absolute clarity, and prevent token waste, follow these instructions:

## 1. Read CONTEXT.md First
At the start of this session, locate and read the `CONTEXT.md` file in the repository root. This file contains the authoritative summary of:
- The project architecture and tech stack.
- Recent changes and current migration status.
- What has been built so far.
- Immediate next steps and planned work.

Use this file to align yourself with the repository structure and history without requiring the user to re-explain it.

## 2. Maintain CONTEXT.md Continuously
Whenever you complete a meaningful task, fix a major bug, or add a new script/feature:
- Update `CONTEXT.md` to reflect these changes under "What This Repo Is" or "Key Features Built" or "File Structure".
- Update the "Migration Status" or "Planned / In Progress" lists (checking off items or adding new ones).
- Keep the "Last updated" date current.

Do not let `CONTEXT.md` fall out of date. It is the source of truth for the next AI session.

## 3. Conserve Tokens & Start Fresh
- When you finish implementing a major feature, explicitly notify the user: *"Task completed. I have updated CONTEXT.md with the latest changes. I recommend opening a fresh chat window to clear the conversation history and start the next task with a clean slate to save tokens."*
- A new, clean chat session will read `CONTEXT.md` at the start, preventing token bloat from long chat histories.
