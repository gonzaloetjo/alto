import type { OrchestratorMode } from "../config/agents.js";

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
export function print(message: string, color?: keyof typeof colors): void {
  if (color && colors[color]) {
    console.log(`${colors[color]}${message}${colors.reset}`);
  } else {
    console.log(message);
  }
}

/**
 * Print a header with mode indicator.
 */
export function printHeader(mode: OrchestratorMode): void {
  const modeColors: Record<OrchestratorMode, keyof typeof colors> = {
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
export function printStatus(
  mode: OrchestratorMode,
  sessionId: string | undefined
): void {
  console.log();
  print("─── ALTO Status ───", "dim");
  console.log(`  Mode:    ${mode}`);
  console.log(`  Session: ${sessionId ?? "(new)"}`);
  console.log();
}

/**
 * Print help for internal commands.
 */
export function printHelp(): void {
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
export function printModeSwitch(
  from: OrchestratorMode,
  to: OrchestratorMode
): void {
  console.log();
  print(`Switching: ${from} → ${to}`, "yellow");
}

/**
 * Print session info.
 */
export function printSessionResume(
  mode: OrchestratorMode,
  sessionId: string
): void {
  print(`Resuming ${mode} session: ${sessionId.slice(0, 8)}...`, "dim");
}

/**
 * Print session start.
 */
export function printSessionStart(mode: OrchestratorMode): void {
  print(`Starting new ${mode} session`, "dim");
}

/**
 * Print error message.
 */
export function printError(message: string): void {
  print(`Error: ${message}`, "red");
}

/**
 * Print warning message.
 */
export function printWarning(message: string): void {
  print(`Warning: ${message}`, "yellow");
}

/**
 * Print success message.
 */
export function printSuccess(message: string): void {
  print(`${message}`, "green");
}

/**
 * Print assistant message.
 */
export function printAssistant(content: string): void {
  console.log();
  console.log(content);
}

/**
 * Print tool use indicator.
 */
export function printToolUse(toolName: string, description?: string): void {
  const desc = description ? ` - ${description}` : "";
  print(`⚙ ${toolName}${desc}`, "dim");
}

/**
 * Format cost in USD.
 */
export function formatCost(costUsd: number): string {
  return `$${costUsd.toFixed(4)}`;
}

/**
 * Print result summary.
 */
export function printResultSummary(
  numTurns: number,
  durationMs: number,
  costUsd: number
): void {
  console.log();
  print("─── Result ───", "dim");
  console.log(`  Turns:    ${numTurns}`);
  console.log(`  Duration: ${(durationMs / 1000).toFixed(1)}s`);
  console.log(`  Cost:     ${formatCost(costUsd)}`);
}
