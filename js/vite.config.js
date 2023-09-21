import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
    build: {
        outDir: path.join(
            __dirname,
            "..",
            "mkdocs_jupyter",
            "templates",
            "mkdocs_html"
        ),
        rollupOptions: {
            input: {
                index: "src/index.js",
                light: "src/theme-light.js",
                dark: "src/theme-dark.js",
            },
            output: {
                entryFileNames: `assets/[name].js`,
                chunkFileNames: `assets/[name].js`,
                assetFileNames: `assets/[name].[ext]`,
            },
        },
    },
});
