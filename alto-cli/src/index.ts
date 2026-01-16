#!/usr/bin/env node

import { Command } from "commander";
import { Alto } from "./alto.js";
import type { OrchestratorMode } from "./config/agents.js";
import { getCurrentMode, setCurrentMode } from "./config/loader.js";
import { SessionManager } from "./session/manager.js";
import { printHeader, printStatus, printError, printSuccess } from "./repl/output.js";

const program = new Command();

program
  .name("alto")
  .description("ALTO CLI - Multi-agent orchestration for Claude Code")
  .version("0.1.0");

// Main command: start interactive REPL
program
  .argument("[prompt]", "Optional initial prompt to run")
  .option("-m, --mode <mode>", "Orchestrator mode (setup|build|dev)")
  .option("-d, --dir <directory>", "Project directory", process.cwd())
  .option("--no-resume", "Start a fresh session instead of resuming")
  .action(async (prompt: string | undefined, options) => {
    const projectDir = options.dir;
    let mode: OrchestratorMode | undefined;

    if (options.mode) {
      if (!["setup", "build", "dev"].includes(options.mode)) {
        printError(`Invalid mode: ${options.mode}. Must be setup, build, or dev.`);
        process.exit(1);
      }
      mode = options.mode as OrchestratorMode;
    }

    // If --no-resume, clear the session first
    if (!options.resume) {
      const sessionManager = new SessionManager(projectDir);
      const currentMode = mode ?? getCurrentMode(projectDir);
      sessionManager.clear(currentMode);
    }

    const alto = new Alto({
      projectDir,
      mode,
    });

    try {
      if (prompt) {
        // Single prompt mode
        const result = await alto.runOnce(prompt);
        console.log(result);
      } else {
        // Interactive REPL mode
        await alto.run();
      }
    } catch (err) {
      printError(`${err}`);
      process.exit(1);
    }
  });

// Subcommand: switch mode
program
  .command("switch <mode>")
  .description("Switch orchestrator mode (setup|build|dev)")
  .option("-d, --dir <directory>", "Project directory", process.cwd())
  .action((mode: string, options) => {
    if (!["setup", "build", "dev"].includes(mode)) {
      printError(`Invalid mode: ${mode}. Must be setup, build, or dev.`);
      process.exit(1);
    }

    setCurrentMode(options.dir, mode as OrchestratorMode);
    printSuccess(`Switched to ${mode} mode`);
  });

// Subcommand: status
program
  .command("status")
  .description("Show current ALTO status")
  .option("-d, --dir <directory>", "Project directory", process.cwd())
  .action((options) => {
    const mode = getCurrentMode(options.dir);
    const sessionManager = new SessionManager(options.dir);
    const sessionId = sessionManager.getSessionId(mode);
    printStatus(mode, sessionId);
  });

// Subcommand: sessions
program
  .command("sessions")
  .description("List all ALTO sessions")
  .option("-d, --dir <directory>", "Project directory", process.cwd())
  .action((options) => {
    const sessionManager = new SessionManager(options.dir);
    const sessions = sessionManager.getAll();

    console.log("\nALTO Sessions:");
    console.log("─────────────────────────────────────");

    if (sessions.size === 0) {
      console.log("  (no sessions)");
    } else {
      for (const [mode, session] of sessions) {
        console.log(`  ${mode.padEnd(6)} ${session.id.slice(0, 8)}...`);
        console.log(`         Created: ${session.createdAt}`);
        console.log(`         Last:    ${session.lastAccessedAt}`);
        console.log();
      }
    }
  });

// Subcommand: clear
program
  .command("clear [mode]")
  .description("Clear session for a mode (or current mode if not specified)")
  .option("-d, --dir <directory>", "Project directory", process.cwd())
  .option("-a, --all", "Clear all sessions")
  .action((mode: string | undefined, options) => {
    const sessionManager = new SessionManager(options.dir);

    if (options.all) {
      sessionManager.clearAll();
      printSuccess("Cleared all sessions");
      return;
    }

    const targetMode = mode
      ? (mode as OrchestratorMode)
      : getCurrentMode(options.dir);

    if (!["setup", "build", "dev"].includes(targetMode)) {
      printError(`Invalid mode: ${targetMode}. Must be setup, build, or dev.`);
      process.exit(1);
    }

    sessionManager.clear(targetMode);
    printSuccess(`Cleared ${targetMode} session`);
  });

program.parse();
