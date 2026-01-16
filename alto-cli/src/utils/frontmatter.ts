import { parse as parseYaml } from "yaml";

export interface FrontmatterResult<T = Record<string, unknown>> {
  data: T;
  content: string;
}

/**
 * Parse YAML frontmatter from markdown content.
 * Frontmatter is delimited by --- at the start of the file.
 */
export function parseFrontmatter<T = Record<string, unknown>>(
  rawContent: string
): FrontmatterResult<T> {
  const trimmed = rawContent.trim();

  // Check if file starts with ---
  if (!trimmed.startsWith("---")) {
    return {
      data: {} as T,
      content: rawContent,
    };
  }

  // Find the closing ---
  const endIndex = trimmed.indexOf("---", 3);
  if (endIndex === -1) {
    return {
      data: {} as T,
      content: rawContent,
    };
  }

  const yamlContent = trimmed.slice(3, endIndex).trim();
  const markdownContent = trimmed.slice(endIndex + 3).trim();

  try {
    const data = parseYaml(yamlContent) as T;
    return {
      data: data ?? ({} as T),
      content: markdownContent,
    };
  } catch {
    // If YAML parsing fails, return empty data
    return {
      data: {} as T,
      content: rawContent,
    };
  }
}
