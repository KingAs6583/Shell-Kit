# Code Review Guidelines

Perform a concise and structured code review of the changes provided. Focus your analysis on the following areas in order of priority:

1. **Correctness & Logic**: Identify syntax errors, logical bugs, edge cases, off-by-one errors, or resource leaks (handles, connections, files).
2. **Security**: Look for vulnerabilities, hardcoded secrets/credentials, injection vectors, or poor permission schemes.
3. **Performance**: Highlight inefficient algorithms, unnecessary iterations, or excessive memory allocations.
4. **Style & Readability**: Suggest improvements for naming conventions, comment clarity, and consistency with standard conventions.

## Output Format
Structure your feedback as a concise bulleted list of actionable findings:
- **[Severity] File:Line** - Description of the issue and a 1-line suggested fix.
  - Severity levels: `Critical` (breaks logic/security), `Warning` (potential bug/perf issue), `Style` (readability).
- If no issues are found, simply output: *"Code review passed. No issues detected."*
