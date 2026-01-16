// ANSI color codes
const colors = {
    reset: "\x1b[0m",
    bold: "\x1b[1m",
    dim: "\x1b[2m",
    red: "\x1b[31m",
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    blue: "\x1b[34m",
    magenta: "\x1b[35m",
    cyan: "\x1b[36m",
    white: "\x1b[37m",
};
/**
 * Print a styled message.
 */
export function print(message, color) {
    if (color && colors[color]) {
        console.log(`${colors[color]}${message}${colors.reset}`);
    }
    else {
        console.log(message);
    }
}
/**
 * Print a header with mode indicator.
 */
export function printHeader(mode) {
    const modeColors = {
        setup: "cyan",
        build: "green",
        dev: "magenta",
    };
    const color = modeColors[mode];
    const modeLabel = mode.toUpperCase();
    console.log();
    print(`╔══════════════════════════════════════╗`, color);
    print(`║          ALTO ${modeLabel.padEnd(7)}              ║`, color);
    print(`╚══════════════════════════════════════╝`, color);
    console.log();
}
/**
 * Print a status message.
 */
export function printStatus(mode, sessionId) {
    console.log();
    print("─── ALTO Status ───", "dim");
    console.log(`  Mode:    ${mode}`);
    console.log(`  Session: ${sessionId ?? "(new)"}`);
    console.log();
}
/**
 * Print help for internal commands.
 */
export function printHelp() {
    console.log();
    print("─── ALTO Commands ───", "dim");
    console.log("  /switch <mode>  Switch orchestrator mode (setup|build|dev)");
    console.log("  /status         Show current mode and session info");
    console.log("  /clear          Clear session for current mode");
    console.log("  /exit           Exit ALTO CLI");
    console.log();
    print("─── Claude Code Commands ───", "dim");
    console.log("  All other /commands are passed to Claude Code");
    console.log();
}
/**
 * Print mode switch message.
 */
export function printModeSwitch(from, to) {
    console.log();
    print(`Switching: ${from} → ${to}`, "yellow");
}
/**
 * Print session info.
 */
export function printSessionResume(mode, sessionId) {
    print(`Resuming ${mode} session: ${sessionId.slice(0, 8)}...`, "dim");
}
/**
 * Print session start.
 */
export function printSessionStart(mode) {
    print(`Starting new ${mode} session`, "dim");
}
/**
 * Print error message.
 */
export function printError(message) {
    print(`Error: ${message}`, "red");
}
/**
 * Print warning message.
 */
export function printWarning(message) {
    print(`Warning: ${message}`, "yellow");
}
/**
 * Print success message.
 */
export function printSuccess(message) {
    print(`${message}`, "green");
}
/**
 * Print assistant message.
 */
export function printAssistant(content) {
    console.log();
    console.log(content);
}
/**
 * Print tool use indicator.
 */
export function printToolUse(toolName, description) {
    const desc = description ? ` - ${description}` : "";
    print(`⚙ ${toolName}${desc}`, "dim");
}
/**
 * Format cost in USD.
 */
export function formatCost(costUsd) {
    return `$${costUsd.toFixed(4)}`;
}
/**
 * Print result summary.
 */
export function printResultSummary(numTurns, durationMs, costUsd) {
    console.log();
    print("─── Result ───", "dim");
    console.log(`  Turns:    ${numTurns}`);
    console.log(`  Duration: ${(durationMs / 1000).toFixed(1)}s`);
    console.log(`  Cost:     ${formatCost(costUsd)}`);
}
//# sourceMappingURL=output.js.map