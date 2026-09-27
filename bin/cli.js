#!/usr/bin/env node
// Installs the /next skill into ~/.claude/skills/next (or $CLAUDE_CONFIG_DIR/skills/next).
//   npx claude-next-skill              install or update
//   npx claude-next-skill uninstall    remove it
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const source = path.join(__dirname, "..", "skills", "next", "SKILL.md");
const configDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
const dir = path.join(configDir, "skills", "next");
const file = path.join(dir, "SKILL.md");
const shown = file.replace(os.homedir(), "~");

const [command = "install", ...rest] = process.argv.slice(2);
const force = rest.includes("--force") || command === "--force";

// A file we can safely replace: an earlier copy of this skill.
function isOurs(text) {
  return /^name:\s*next\s*$/m.test(text) && text.includes("disable-model-invocation: true") && text.includes("$ARGUMENTS");
}

function fail(message) {
  console.error(`✗ ${message}`);
  process.exit(1);
}

function install() {
  const skill = fs.readFileSync(source, "utf8");
  const link = fs.lstatSync(dir, { throwIfNoEntry: false });
  if (link && link.isSymbolicLink()) {
    fail(`${dir.replace(os.homedir(), "~")} is a symlink to ${fs.readlinkSync(dir)}. Left it alone.`);
  }
  const existed = fs.existsSync(file);
  if (existed) {
    const current = fs.readFileSync(file, "utf8");
    if (current === skill) {
      console.log(`✓ /next is already up to date (${shown})`);
      return;
    }
    if (!isOurs(current) && !force) {
      fail(`${shown} already holds a different "next" skill. Run again with --force to replace it.`);
    }
  }
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(file, skill);
  console.log(`✓ ${existed ? "Updated" : "Installed"} /next → ${shown}`);
  console.log("  Open a new Claude Code session. While Claude is working, type: /next <your next request>");
}

function uninstall() {
  if (!fs.existsSync(file)) {
    console.log(`✓ Nothing to remove (${shown} doesn't exist)`);
    return;
  }
  if (!isOurs(fs.readFileSync(file, "utf8")) && !force) {
    fail(`${shown} isn't the /next skill from this package. Run again with --force to remove it anyway.`);
  }
  fs.rmSync(file);
  if (fs.readdirSync(dir).length === 0) fs.rmdirSync(dir);
  console.log(`✓ Removed /next (${shown})`);
}

switch (command) {
  case "install":
  case "--force":
    install();
    break;
  case "uninstall":
  case "remove":
    uninstall();
    break;
  case "help":
  case "--help":
  case "-h":
    console.log("Usage: npx claude-next-skill [install|uninstall] [--force]");
    break;
  default:
    fail(`Unknown command "${command}". Try: npx claude-next-skill --help`);
}
