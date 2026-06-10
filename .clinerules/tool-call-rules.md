# Tool Call Rules for Cline

## Critical Rule: Every Response MUST Contain a Tool Call

**Problem Discovered**: When Cline writes text describing what tool to use (e.g., "Now I will use write_to_file to..."), the system returns "You did not use a tool in your previous response". This happens because the tool call XML block is NOT being emitted — only the text description is sent.

## Rules to Follow

1. **NEVER describe a tool call in text without actually invoking it.** Do not write sentences like:
   - "Now I will use write_to_file..."
   - "Let me update the file using replace_in_file..."
   - "I'll create this file..."
   These phrases WITHOUT an actual tool invocation block cause the "did not use a tool" error.

2. **Every response that requires an action MUST include exactly one tool call block.** If you need to perform multiple operations, chain them — do one per response and wait for the result.

3. **Do NOT mix text descriptions of tool usage with actual tool calls in ambiguous ways.** Either:
   - Write pure text explanation (no tool)
   - Write explanation + actual tool call block (tool is invoked)

4. **When the system says "You did not use a tool", immediately invoke a tool on the next response.** Do not write text explaining why you failed to call a tool — just call the tool.

5. **Short responses are fine.** A response that contains only a tool call (with no preceding text) is valid and preferred when the action is clear.

## Pattern to Follow

**WRONG** (causes repeated "did not use a tool" errors):
```
Now I will update the file to fix the issue:
[no actual tool call block follows]
```

**CORRECT**:
```
[tool call block immediately, optionally preceded by very brief explanation]
```

## Summary

The core issue is that writing about tool usage ≠ performing tool usage. The tool call must be an actual XML/function invocation block in the response, not a text description of intent.
