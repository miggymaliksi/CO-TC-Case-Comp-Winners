const { packager } = require("@electron/packager");
const fs = require("node:fs/promises");
const path = require("node:path");

async function build() {
  if (process.platform !== "darwin")
    throw new Error("Build the Mac demo on a Mac.");
  const root = path.resolve(__dirname, "..");
  await fs.access(path.join(root, ".venv/bin/python"));
  await fs.access(path.join(root, "frontend/dist/index.html"));
  const stage = path.join(__dirname, ".stage");
  await fs.mkdir(stage, { recursive: true });
  for (const name of ["main.cjs", "server.py", "loading.html"]) {
    await fs.copyFile(path.join(__dirname, name), path.join(stage, name));
  }
  await fs.copyFile(
    path.join(root, "frontend/src/assets/savor-logo.png"),
    path.join(stage, "savor-logo.png"),
  );
  const source = JSON.parse(
    await fs.readFile(path.join(__dirname, "package.json"), "utf8"),
  );
  const { devDependencies, scripts, ...manifest } = source;
  await fs.writeFile(
    path.join(stage, "package.json"),
    JSON.stringify(manifest, null, 2),
  );
  // This is deliberately a launcher for the prepared checkout, not a portable installer.
  await fs.writeFile(
    path.join(stage, "checkout.json"),
    JSON.stringify({ root }),
  );
  const output = await packager({
    dir: stage,
    name: "Savor",
    platform: "darwin",
    arch: process.arch,
    electronVersion: source.devDependencies.electron,
    appBundleId: "com.savor.localdemo",
    appCategoryType: "public.app-category.food-and-drink",
    asar: true,
    extraResource: path.join(__dirname, "server.py"),
    out: path.join(__dirname, "release"),
    overwrite: true,
    icon: path.join(__dirname, "icon.icns"),
    extendInfo: { NSHumanReadableCopyright: "Savor case competition demo" },
  });
  console.log(`Open ${path.join(output[0], "Savor.app")}`);
}

build().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
