# RESSL Assignment Implementation

This repository collects deliverables for the RESSL assignment. It covers both the Salesforce setup task and the MCP keyword search server.

## Task 1 – Salesforce Setup

Complete these steps in your Salesforce Developer Edition environment:

1. Sign up for a free [Salesforce Developer Edition](https://developer.salesforce.com/signup) account.
2. Create a custom object (e.g., `Project__c`) with at least one custom field.
3. Add the custom object as a tab so it is visible in the Salesforce UI.
4. Create a sample record for the new custom object.
5. Capture a screenshot showing the record detail page. Attach that screenshot to your submission document.

> **Note:** The automation in this repository does not interact with Salesforce. Perform the steps manually in your org, then store the screenshot alongside your final report.

## Task 2 – MCP Keyword Search Server

The `keyword-search-server` exposes a single MCP tool that scans a text file for a keyword and returns all matches with optional context. The implementation uses the official [`@modelcontextprotocol/sdk`](https://www.npmjs.com/package/@modelcontextprotocol/sdk).

### Prerequisites

- Node.js 20+
- npm 9+

Install project dependencies:

```cmd
npm install
```

### Available Scripts

| Command           | Description |
|-------------------|-------------|
| `npm run build`   | Type-checks and emits the compiled JavaScript to `dist/`. |
| `npm run start`   | Runs the compiled server via `node dist/server.js`. Use after `npm run build`. |
| `npm run dev`     | Starts the server with live TypeScript reloading via `tsx watch`. |

### Running the Server (stdio)

1. Build the project: `npm run build`
2. Launch the stdio transport server: `npm run start`

This keeps the server listening on stdin/stdout, ready for a client such as MCP Inspector.

### Connecting with MCP Inspector

1. In a separate terminal, install the inspector if you do not already have it:
   ```cmd
   npx @modelcontextprotocol/inspector@latest --help
   ```
2. With the server running, start the inspector and connect over stdio:
   ```cmd
   npx @modelcontextprotocol/inspector@latest --stdio
   ```
3. Trigger the `keyword-search` tool with inputs similar to:
   ```json
   {
     "filePath": "README.md",
     "keyword": "MCP",
     "caseSensitive": false,
     "maxMatches": 20,
     "contextLines": 1
   }
   ```
4. Capture a screenshot showing the inspector input and output for inclusion in your report.

### Sample Output Structure

Tool invocations return a JSON payload:

```json
{
  "totalMatches": 2,
  "matches": [
    {
      "lineNumber": 5,
      "column": 10,
      "line": "Sample line containing MCP.",
      "contextBefore": ["Previous line"],
      "contextAfter": ["Next line"]
    }
  ]
}
```

The same payload is included as structured content in the MCP response, allowing clients to consume it programmatically.

## Repository Structure

```
src/server.ts   # MCP server entry point
README.md       # Assignment documentation (this file)
```

## Next Steps

- Attach the requested Salesforce screenshot and MCP Inspector screenshot to your deliverable document.
- Push this project to GitHub and include the repository link in your submission.
