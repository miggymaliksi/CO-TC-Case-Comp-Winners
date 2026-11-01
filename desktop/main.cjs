const { app, BrowserWindow, dialog, Menu, screen, shell } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const readline = require("node:readline");

const root = app.isPackaged
  ? JSON.parse(fs.readFileSync(path.join(__dirname, "checkout.json"), "utf8"))
      .root
  : path.resolve(__dirname, "..");
const cache = path.join(root, ".desktop-data");
fs.mkdirSync(cache, { recursive: true });
app.setPath("userData", path.join(cache, "profile"));

let window;
let backend;
let quitting = false;
let stopping = false;

function showWindow() {
  if (window && !window.isDestroyed()) {
    if (window.isMinimized()) window.restore();
    window.show();
    window.focus();
    if (process.platform === "darwin") app.focus({ steal: true });
  }
}

function healthy(port) {
  return new Promise((resolve) => {
    const request = http.get(
      `http://127.0.0.1:${port}/api/health`,
      { timeout: 1000 },
      (response) => {
        let body = "";
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          try {
            const result = JSON.parse(body);
            resolve(
              response.statusCode === 200 &&
                result.ok &&
                result.mode === "local sample accounts",
            );
          } catch {
            resolve(false);
          }
        });
      },
    );
    request.on("timeout", () => request.destroy());
    request.on("error", () => resolve(false));
  });
}

async function startBackend() {
  const python = path.join(root, ".venv", "bin", "python");
  if (
    !fs.existsSync(python) ||
    !fs.existsSync(path.join(root, "frontend/dist/index.html"))
  ) {
    throw new Error(
      "Open the Savor project in VS Code and run its setup first: python3 run.py --prepare. Keep this project folder in place after building the Mac app.",
    );
  }
  const log = fs.openSync(path.join(cache, "server.log"), "a");
  // Pass only runtime essentials; no API keys or arbitrary database/host overrides.
  const env = { PYTHONUNBUFFERED: "1" };
  for (const key of [
    "PATH",
    "HOME",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "SYSTEMROOT",
  ]) {
    if (process.env[key]) env[key] = process.env[key];
  }
  const service = app.isPackaged
    ? path.join(process.resourcesPath, "server.py")
    : path.join(__dirname, "server.py");
  backend = spawn(python, [service, root], {
    cwd: root,
    env,
    stdio: ["ignore", "pipe", log],
  });
  fs.closeSync(log);
  const port = await new Promise((resolve, reject) => {
    const timer = setTimeout(
      () =>
        reject(
          new Error(
            "Savor took too long to start. See .desktop-data/server.log in the project folder.",
          ),
        ),
      45000,
    );
    const lines = readline.createInterface({ input: backend.stdout });
    lines.on("line", (line) => {
      const match = /^SAVOR_DESKTOP_PORT=(\d+)$/.exec(line);
      if (match) {
        clearTimeout(timer);
        resolve(Number(match[1]));
      }
    });
    backend.once("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    backend.once("exit", () => {
      clearTimeout(timer);
      reject(
        new Error(
          "Savor's local service stopped during startup. Check .desktop-data/server.log in the project folder.",
        ),
      );
    });
  });
  const deadline = Date.now() + 45000;
  while (!(await healthy(port))) {
    if (quitting) throw new Error("Savor is closing.");
    if (backend.exitCode !== null || Date.now() > deadline) {
      throw new Error(
        "Savor could not open its local service. Check .desktop-data/server.log in the project folder, then try again.",
      );
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  backend.on("exit", () => {
    if (!quitting) {
      dialog.showErrorBox(
        "Savor stopped",
        "The local service stopped. Close and reopen Savor to try again. Your saved pantry stays in the project folder.",
      );
      app.quit();
    }
  });
  return `http://127.0.0.1:${port}`;
}

async function openWindow() {
  const available = screen.getPrimaryDisplay().workAreaSize;
  window = new BrowserWindow({
    title: "Savor",
    width: 402,
    height: Math.min(844, available.height - 48),
    useContentSize: true,
    minWidth: 360,
    maxWidth: 480,
    minHeight: 560,
    maximizable: false,
    fullscreenable: false,
    backgroundColor: "#f8f8f3",
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webviewTag: false,
    },
  });
  window.once("ready-to-show", showWindow);
  window.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const source = new URL(url);
      if (
        source.protocol === "https:" &&
        source.host === "www.themealdb.com" &&
        /^\/meal\/\d{1,12}$/.test(source.pathname) &&
        !source.search &&
        !source.hash &&
        !source.username &&
        !source.password
      ) {
        shell.openExternal(source.href).catch(() => {});
      }
    } catch {}
    return { action: "deny" };
  });
  const session = window.webContents.session;
  session.setPermissionRequestHandler((_contents, permission, callback) => {
    callback(permission === "clipboard-sanitized-write");
  });
  session.setPermissionCheckHandler(
    (_contents, permission) => permission === "clipboard-sanitized-write",
  );
  await window.loadFile(path.join(__dirname, "loading.html"));
  if (quitting) return;
  const origin = await startBackend();
  const allowNavigation = (event, url) => {
    if (new URL(url).origin !== origin) event.preventDefault();
  };
  window.webContents.on("will-navigate", allowNavigation);
  window.webContents.on("will-redirect", allowNavigation);
  session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [
          "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://www.themealdb.com; connect-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'self'; form-action 'self'",
        ],
      },
    });
  });
  if (!quitting && !window.isDestroyed()) await window.loadURL(origin);
}

if (!app.requestSingleInstanceLock()) {
  console.log("Savor is already open. Bringing the existing window forward.");
  app.quit();
} else {
  console.log("Opening Savor. Close its window when you are finished.");
  app.on("second-instance", showWindow);
  app.on("activate", showWindow);
  // Gracefully stop owned services when a development terminal is interrupted too.
  process.on("SIGTERM", () => app.quit());
  process.on("SIGINT", () => app.quit());
  app.whenReady().then(async () => {
    if (!app.isPackaged) {
      // The splash page uses the same original artwork as the React interface.
      fs.copyFileSync(
        path.join(root, "frontend/src/assets/savor-logo.png"),
        path.join(__dirname, "savor-logo.png"),
      );
    }
    if (process.platform === "darwin") {
      app.dock.setIcon(path.join(root, "frontend/src/assets/savor-icon.png"));
    }
    Menu.setApplicationMenu(
      Menu.buildFromTemplate([
        {
          label: "Savor",
          submenu: [{ role: "about" }, { type: "separator" }, { role: "quit" }],
        },
        { role: "editMenu" },
        { role: "windowMenu" },
        {
          label: "View",
          submenu: [
            { role: "reload" },
            { role: "resetZoom" },
            { role: "zoomIn" },
            { role: "zoomOut" },
          ],
        },
      ]),
    );
    try {
      await openWindow();
    } catch (error) {
      if (!quitting) dialog.showErrorBox("Couldn't open Savor", error.message);
      app.quit();
    }
  });
  // A phone demo should actually stop when its only window closes.
  app.on("window-all-closed", () => app.quit());
  app.on("before-quit", (event) => {
    quitting = true;
    if (backend && backend.exitCode === null && !stopping) {
      event.preventDefault();
      stopping = true;
      const timer = setTimeout(() => {
        backend.kill("SIGKILL");
        app.quit();
      }, 15000);
      backend.once("exit", () => {
        clearTimeout(timer);
        app.quit();
      });
      backend.kill("SIGTERM");
    }
  });
}
