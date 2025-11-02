import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { promises as fs } from 'node:fs';
import path from 'node:path';

// Set up the MCP server metadata
const server = new McpServer(
  {
    name: 'keyword-search-server',
    version: '0.1.0'
  },
  {
    instructions:
      'Provide a file path and keyword to receive all matches with context. Optional flags allow case-sensitive search, match limits, and line context.'
  }
);

const keywordSearchInputSchema = {
  filePath: z
    .string()
    .min(1)
    .describe('Absolute or relative path to the text file that should be searched.'),
  keyword: z.string().min(1).describe('Keyword or phrase to search for within the file.'),
  caseSensitive: z
    .boolean()
    .optional()
    .default(false)
    .describe('If true, the search is case-sensitive. Defaults to false.'),
  maxMatches: z
    .number()
    .int()
    .positive()
    .max(500)
    .optional()
    .default(50)
    .describe('Maximum number of matches to return. Defaults to 50. Upper bound of 500 to protect performance.'),
  contextLines: z
    .number()
    .int()
    .min(0)
    .max(10)
    .optional()
    .default(0)
    .describe('Number of surrounding lines to include before and after each match (0-10).')
};

const keywordSearchOutputSchema = {
  totalMatches: z
    .number()
    .int()
    .nonnegative()
    .describe('Total number of matches found (capped by maxMatches).'),
  matches: z
    .array(
      z.object({
        lineNumber: z.number().int().positive().describe('1-based line number of the match.'),
        column: z.number().int().positive().describe('1-based column index where the keyword begins.'),
        line: z.string().describe('Full line containing the match.'),
        contextBefore: z
          .array(z.string())
          .describe('Lines of context that precede the match (from oldest to newest).'),
        contextAfter: z
          .array(z.string())
          .describe('Lines of context that follow the match (from earliest to latest).')
      })
    )
    .describe('Matches that were captured by the search operation.')
};

server.registerTool(
  'keyword-search',
  {
    title: 'Keyword Search',
    description: 'Search for a keyword within a text file and return matches with surrounding context.',
    inputSchema: keywordSearchInputSchema,
    outputSchema: keywordSearchOutputSchema
  },
  async ({ filePath, keyword, caseSensitive = false, maxMatches = 50, contextLines = 0 }) => {
    const targetPath = path.resolve(process.cwd(), filePath);
    const statistics = await fs.stat(targetPath).catch(() => {
      throw new Error(`File not found or inaccessible: ${targetPath}`);
    });

    if (!statistics.isFile()) {
      throw new Error(`Path is not a file: ${targetPath}`);
    }

    const rawContent = await fs.readFile(targetPath, 'utf8');
    const lines = rawContent.split(/\r?\n/);
    const normalizedKeyword = caseSensitive ? keyword : keyword.toLowerCase();

    const matches: Array<{
      lineNumber: number;
      column: number;
      line: string;
      contextBefore: string[];
      contextAfter: string[];
    }> = [];

    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      const candidate = caseSensitive ? line : line.toLowerCase();

      let searchStart = 0;
      while (searchStart <= candidate.length) {
        const matchIndex = candidate.indexOf(normalizedKeyword, searchStart);
        if (matchIndex === -1) {
          break;
        }

        const contextBefore = contextLines
          ? lines.slice(Math.max(0, index - contextLines), index)
          : [];
        const contextAfter = contextLines
          ? lines.slice(index + 1, Math.min(lines.length, index + 1 + contextLines))
          : [];

        matches.push({
          lineNumber: index + 1,
          column: matchIndex + 1,
          line,
          contextBefore,
          contextAfter
        });

        if (matches.length >= maxMatches) {
          break;
        }

        searchStart = matchIndex + normalizedKeyword.length;
      }

      if (matches.length >= maxMatches) {
        break;
      }
    }

    const result = {
      totalMatches: matches.length,
      matches
    };

    return {
      structuredContent: result,
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  let shuttingDown = false;
  const shutdown = async () => {
    if (shuttingDown) {
      return;
    }
    shuttingDown = true;
    await server.close();
    await transport.close();
  };

  process.on('SIGINT', async () => {
    await shutdown();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await shutdown();
    process.exit(0);
  });
}

main().catch(error => {
  console.error('Keyword search MCP server failed to start:', error);
  process.exit(1);
});
