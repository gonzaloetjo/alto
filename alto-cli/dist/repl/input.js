import * as readline from "node:readline";
/**
 * Parse internal ALTO commands from user input.
 */
function parseCommand(input) {
    const trimmed = input.trim();
    // /switch <mode>
    if (trimmed.startsWith("/switch ")) {
        const mode = trimmed.slice(8).trim();
        if (mode === "setup" || mode === "build" || mode === "dev") {
            return { type: "switch", mode };
        }
        return null;
    }
    // /status
    if (trimmed === "/status") {
        return { type: "status" };
    }
    // /exit or /quit
    if (trimmed === "/exit" || trimmed === "/quit") {
        return { type: "exit" };
    }
    // /clear
    if (trimmed === "/clear") {
        return { type: "clear" };
    }
    return null;
}
/**
 * Create an SDK-compatible user message.
 * The SDK fills in session_id when processing the stream.
 */
function createUserMessage(content) {
    // Cast is needed because the SDK type requires session_id but
    // the SDK fills it in when processing streaming input
    return {
        type: "user",
        session_id: "",
        message: {
            role: "user",
            content,
        },
        parent_tool_use_id: null,
    };
}
/**
 * Create an async generator that yields user messages from stdin.
 * Handles internal /switch, /status, /exit commands.
 */
export async function* createInputGenerator(currentMode, onCommand) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: true,
    });
    const prompt = () => {
        const modeLabel = currentMode.toUpperCase();
        process.stdout.write(`\n[${modeLabel}] > `);
    };
    prompt();
    for await (const line of rl) {
        const input = line.trim();
        if (!input) {
            prompt();
            continue;
        }
        // Check for internal commands
        const command = parseCommand(input);
        if (command) {
            const shouldContinue = await onCommand(command);
            if (!shouldContinue) {
                rl.close();
                return;
            }
            prompt();
            continue;
        }
        // Yield user message to SDK
        yield createUserMessage(input);
        // Prompt will be shown after SDK response
    }
    rl.close();
}
/**
 * Simple readline prompt for single input.
 */
export function promptUser(question) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            rl.close();
            resolve(answer.trim());
        });
    });
}
//# sourceMappingURL=input.js.map