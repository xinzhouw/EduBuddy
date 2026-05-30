## Terminal & Workspace Execution Rules

To prevent terminal locking, shell integration hangs, or command collision during full-stack development, the AI Assistant MUST strictly follow this multi-terminal allocation strategy:

1. **Terminal 1 (Frontend):** Dedicated exclusively to running the frontend development server (e.g., `npm run dev`). Once started, do NOT execute any other commands here.
2. **Terminal 2 (Backend):** Dedicated exclusively to running the backend server/API service. Once started, do NOT execute any other commands here.
3. **Terminal 3+ (Execution & Testing):** Create a brand-new, clean terminal for ALL subsequent tasks, including:
   - Running code modifications, file scripts, or Git operations.
   - Executing test scripts, `curl` health checks, or build validation.
   - Running temporary diagnostic commands.

*Note: Never attempt to "piggyback" or inject background commands into Terminal 1 or Terminal 2 while they are hosting active server processes.*