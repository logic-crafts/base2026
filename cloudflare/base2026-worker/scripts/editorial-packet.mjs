#!/usr/bin/env node

/** Local validation/packing only. This CLI has no publication transport. */
import { constants } from "node:fs";
import { lstat, open, readFile, realpath } from "node:fs/promises";
import { dirname, isAbsolute, normalize } from "node:path";

const INPUT_LIMITS = Object.freeze({ payload: 256 * 1024, review: 4 * 1024 });

class CliError extends Error {
  constructor(code, details = {}) {
    super(code);
    this.code = code;
    this.details = details;
  }
}

function argumentsFor(argv) {
  const [command, ...args] = argv;
  const flags = command === "validate" ? ["--payload"]
    : command === "pack" ? ["--payload", "--review", "--out"] : null;
  if (!flags || args.length !== flags.length * 2) throw new CliError("EDITORIAL_CLI_ARGUMENTS_INVALID");
  const options = {};
  for (let index = 0; index < args.length; index += 2) {
    const flag = args[index];
    if (!flags.includes(flag) || Object.hasOwn(options, flag)) throw new CliError("EDITORIAL_CLI_ARGUMENTS_INVALID");
    const value = args[index + 1];
    if (typeof value !== "string" || value.length > 4_096 || !isAbsolute(value)
      || normalize(value) !== value || /[\u0000-\u001f\u007f]/u.test(value)) {
      throw new CliError("EDITORIAL_CLI_PATH_INVALID");
    }
    options[flag] = value;
  }
  return { command, payload: options["--payload"], review: options["--review"], out: options["--out"] };
}

async function assertRealParent(path) {
  // Refuse directory aliases too; callers must supply real absolute paths.
  if (await realpath(dirname(path)) !== dirname(path)) throw new CliError("EDITORIAL_CLI_SYMLINK_REFUSED");
}

async function readObject(path, field) {
  const limit = INPUT_LIMITS[field];
  let handle;
  try {
    await assertRealParent(path);
    const entry = await lstat(path);
    if (entry.isSymbolicLink()) throw new CliError("EDITORIAL_CLI_SYMLINK_REFUSED", { field });
    if (!entry.isFile()) throw new CliError("EDITORIAL_CLI_INPUT_NOT_REGULAR", { field });
    if (constants.O_NOFOLLOW === undefined || constants.O_NONBLOCK === undefined) {
      throw new CliError("EDITORIAL_CLI_RUNTIME_UNSUPPORTED");
    }
    // O_NOFOLLOW closes the leaf-symlink race; NONBLOCK avoids opening a FIFO
    // indefinitely if a regular input is replaced after the initial lstat.
    handle = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
    const before = await handle.stat();
    if (!before.isFile()) throw new CliError("EDITORIAL_CLI_INPUT_NOT_REGULAR", { field });
    if (before.size > limit) throw new CliError("EDITORIAL_CLI_INPUT_TOO_LARGE", { field });
    const bytes = Buffer.alloc(limit + 1);
    let length = 0;
    while (length < bytes.length) {
      const { bytesRead } = await handle.read(bytes, length, bytes.length - length, length);
      if (bytesRead === 0) break;
      length += bytesRead;
    }
    if (length > limit) throw new CliError("EDITORIAL_CLI_INPUT_TOO_LARGE", { field });
    const after = await handle.stat();
    if (before.size !== length || after.size !== length || before.mtimeMs !== after.mtimeMs
      || before.ctimeMs !== after.ctimeMs) throw new CliError("EDITORIAL_CLI_INPUT_CHANGED", { field });
    let value;
    try {
      const json = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes.subarray(0, length));
      value = JSON.parse(json);
    } catch {
      // JSON/UTF-8 parser errors can contain input excerpts. Never print them.
      throw new CliError("EDITORIAL_CLI_JSON_INVALID", { field });
    }
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      throw new CliError("EDITORIAL_CLI_OBJECT_REQUIRED", { field });
    }
    return value;
  } catch (error) {
    if (error instanceof CliError) throw error;
    if (error?.code === "ELOOP") throw new CliError("EDITORIAL_CLI_SYMLINK_REFUSED", { field });
    throw new CliError("EDITORIAL_CLI_INPUT_UNREADABLE", { field });
  } finally {
    await handle?.close();
  }
}

async function validator() {
  try {
    // Only these two fixed repository modules are executable. User JSON never
    // becomes code or an import path. Compile the dependency first, in memory;
    // no tsconfig, arbitrary module resolver or generated disk files are used.
    const { default: ts } = await import("typescript");
    let dependencyUrl;
    let entryUrl;
    for (const name of ["evidence-dependencies.ts", "editorial.ts"]) {
      const source = await readFile(new URL("../src/" + name, import.meta.url), "utf8");
      const compiled = ts.transpileModule(source, {
        fileName: name,
        reportDiagnostics: true,
        compilerOptions: {
          target: ts.ScriptTarget.ES2022,
          module: ts.ModuleKind.ESNext,
          removeComments: true,
          sourceMap: false,
          inlineSourceMap: false,
        },
      });
      if (compiled.diagnostics?.some((item) => item.category === ts.DiagnosticCategory.Error)) throw new Error();
      const imports = ts.preProcessFile(compiled.outputText, true, true).importedFiles;
      let executable = compiled.outputText;
      if (name === "evidence-dependencies.ts") {
        if (imports.length) throw new Error();
      } else if (imports.length === 1 && imports[0].fileName === "./evidence-dependencies" && dependencyUrl) {
        const fixedImport = /from\s*(["'])\.\/evidence-dependencies\1/gu;
        if ([...executable.matchAll(fixedImport)].length !== 1) throw new Error();
        executable = executable.replace(fixedImport, () => "from " + JSON.stringify(dependencyUrl));
      } else if (imports.length) throw new Error();
      const url = `data:text/javascript;base64,${Buffer.from(executable).toString("base64")}`;
      if (name === "evidence-dependencies.ts") dependencyUrl = url;
      else entryUrl = url;
    }
    const loaded = await import(entryUrl);
    return {
      validateEditorialPayload: loaded.validateEditorialPayload,
      validateEditorialPacket: loaded.validateEditorialPacket,
      editorialArticlePath: loaded.editorialArticlePath,
    };
  } catch {
    throw new CliError("EDITORIAL_CLI_VALIDATOR_UNAVAILABLE");
  }
}

async function createPacket(path, value) {
  let handle;
  const serialized = `${JSON.stringify(value, null, 2)}\n`;
  try {
    await assertRealParent(path);
    // wx refuses existing files, directories and leaf symlinks atomically.
    // A write failure may leave an incomplete new file; never remove/replace
    // it automatically or claim that it is a successfully packed candidate.
    handle = await open(path, "wx", 0o600);
    await handle.writeFile(serialized, "utf8");
    await handle.sync();
  } catch (error) {
    if (error instanceof CliError) throw error;
    if (error?.code === "EEXIST" || error?.code === "ELOOP") throw new CliError("EDITORIAL_CLI_OUTPUT_EXISTS");
    throw new CliError("EDITORIAL_CLI_OUTPUT_WRITE_FAILED");
  } finally {
    await handle?.close();
  }
  return Buffer.byteLength(serialized, "utf8");
}

async function run(argv) {
  const options = argumentsFor(argv);
  const payload = await readObject(options.payload, "payload");
  // No review file, reviewer, outcome or approval time is synthesized here.
  const review = options.command === "pack" ? await readObject(options.review, "review") : undefined;
  const api = await validator();
  const now = new Date().toISOString();
  const result = options.command === "pack"
    ? await api.validateEditorialPacket({ payload, review }, now)
    : await api.validateEditorialPayload(payload, now);
  if (!result.ok) throw new CliError("EDITORIAL_CLI_VALIDATION_FAILED", { issues: result.issues });
  const publicPath = api.editorialArticlePath(result.payload.slug, result.payload.kind);
  if (options.command === "validate") {
    return { ok: true, payload_sha256: result.payload_sha256, diagnostics: result.diagnostics, public_path: publicPath };
  }
  const packetBytes = await createPacket(options.out, { payload: result.payload, review: result.review });
  return { ok: true, status: "packed", payload_sha256: result.payload_sha256, public_path: publicPath, output_path: options.out, packet_bytes: packetBytes };
}

// Importing this module performs no CLI work, file reads or compiler load.
if (import.meta.main) {
  try {
    process.stdout.write(`${JSON.stringify(await run(process.argv.slice(2)))}\n`);
  } catch (error) {
    const receipt = error instanceof CliError
      ? { ok: false, code: error.code, ...error.details }
      : { ok: false, code: "EDITORIAL_CLI_FAILED" };
    process.stderr.write(`${JSON.stringify(receipt)}\n`);
    process.exitCode = 1;
  }
}
