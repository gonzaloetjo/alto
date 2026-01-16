import { parse as parseYaml } from "yaml";
/**
 * Parse YAML frontmatter from markdown content.
 * Frontmatter is delimited by --- at the start of the file.
 */
export function parseFrontmatter(rawContent) {
    const trimmed = rawContent.trim();
    // Check if file starts with ---
    if (!trimmed.startsWith("---")) {
        return {
            data: {},
            content: rawContent,
        };
    }
    // Find the closing ---
    const endIndex = trimmed.indexOf("---", 3);
    if (endIndex === -1) {
        return {
            data: {},
            content: rawContent,
        };
    }
    const yamlContent = trimmed.slice(3, endIndex).trim();
    const markdownContent = trimmed.slice(endIndex + 3).trim();
    try {
        const data = parseYaml(yamlContent);
        return {
            data: data ?? {},
            content: markdownContent,
        };
    }
    catch {
        // If YAML parsing fails, return empty data
        return {
            data: {},
            content: rawContent,
        };
    }
}
//# sourceMappingURL=frontmatter.js.map