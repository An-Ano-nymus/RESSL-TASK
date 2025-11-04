## RESSL Tasks

This repository contains a Python-based Model Context Protocol (MCP) server that fulfils Task 2 of the Ressl assignment. The server exposes a single tool, `search_keyword`, which scans UTF-8 text files for keyword occurrences and returns formatted matches with line numbers.

### Prerequisites
- Python 3.10+
- `pip` (bundled with Python)

### Setup
- (Recommended) Create and activate a virtual environment inside the repo root.
- Install dependencies: `pip install -r requirements.txt`

### Run the MCP Server
```cmd
python python\keyword_search_mcp_server.py --workspace-root .
```
- The `--workspace-root` flag defaults to the current directory. Override it if you want to restrict searches to a different folder. Alternatively, set the `RESSL_WORKSPACE_ROOT` environment variable before launching the server.

### Tool Reference: `search_keyword`
- **Parameters**
	- `file_path` (str): Relative or absolute path to the UTF-8 text file.
	- `keyword` (str): Search term (required, non-empty).
	- `case_sensitive` (bool, default `false`): Toggle case-sensitive search.
	- `max_matches` (int, default `20`): Limit the number of reported matches (min 1).
- **Output**
	- Two `text` blocks on success: a summary line and a list of `line_number: context` entries with the first occurrence highlighted as `[match]`.
	- A single `text` block stating that no matches were found when applicable.

### Testing with MCP Inspector
1. Launch the server (see command above).
2. Open [MCP Inspector](https://github.com/modelcontextprotocol/inspector) and create a connection that targets the running stdio server.
3. Call the `search_keyword` tool with sample input, e.g.
	 ```json
	 {
		 "file_path": "README.md",
		 "keyword": "MCP",
		 "case_sensitive": false,
		 "max_matches": 5
	 }
	 ```
4. Confirm that the tool response lists the matching lines.

### Screenshots
- ![Inspector launch](Screenshot%202025-11-02%20235351.png)
- ![Tool configuration](Screenshot%202025-11-04%20094254.png)
- ![Tool invocation form](Screenshot%202025-11-04%20094353.png)
- ![Tool response](Screenshot%202025-11-04%20094402.png)

### Repository Link
- https://github.com/An-Ano-nymus/RESSL-TASK
