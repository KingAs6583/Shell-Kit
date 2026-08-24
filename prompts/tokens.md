# Token-Saving Guidelines for AI Coding Assistants

To keep our conversation token-efficient, fast, and cost-effective, you must adhere to the following guidelines:

## 1. Do Not Output Full Files
- When modifying code, never output the entire modified file.
- Use git-style **diff blocks** (`+` for additions, `-` for deletions) or output only the specific functions/blocks of code that changed.
- Keep the unmodified context lines to a minimum (1-2 lines before and after).

## 2. Be Extremely Concise
- Keep explanations to a minimum. Focus on *why* a change was made rather than describing *what* the lines of code do (the code speaks for itself).
- Do not repeat or re-summarize what was agreed upon in the plan or instructions.

## 3. Don't Loop or Poll
- Do not poll command outputs or run scripts in loops. If a task is running asynchronously, explain how to check it, or wait for the system notification.
- Stop calling tools and yield control to the user if you are waiting for their input or verification.

## 4. Ask Early
- If requirements are ambiguous or you are unsure about the codebase structure, ask a single clarifying question instead of writing hypothetical code that may be wrong and waste tokens.
