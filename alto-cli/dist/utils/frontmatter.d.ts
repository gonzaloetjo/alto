export interface FrontmatterResult<T = Record<string, unknown>> {
    data: T;
    content: string;
}
/**
 * Parse YAML frontmatter from markdown content.
 * Frontmatter is delimited by --- at the start of the file.
 */
export declare function parseFrontmatter<T = Record<string, unknown>>(rawContent: string): FrontmatterResult<T>;
//# sourceMappingURL=frontmatter.d.ts.map