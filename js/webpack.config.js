var path = require("path")
const FileManagerPlugin = require("filemanager-webpack-plugin")
const FixStyleOnlyEntriesPlugin = require("webpack-fix-style-only-entries")
const MiniCssExtractPlugin = require("mini-css-extract-plugin")

const extractPlugin = {
    loader: MiniCssExtractPlugin.loader,
}

const pythonPkgStatic = path.resolve(
    __dirname,
    "..",
    "mkdocs_jupyter",
    "templates",
    "mkdocs_html",
    "assets"
)

module.exports = (env, argv) => {
    const IS_PRODUCTION = argv.mode === "production"

    const config_lib = {
        entry: path.resolve(__dirname, "src", "index.js"),
        output: {
            path: path.resolve(pythonPkgStatic),
            filename: "mkdocs-jupyter.js",
        },
        module: {
            rules: [
                {
                    test: /\.(js)$/,
                    exclude: /node_modules/,
                },
                {
                    test: /\.s?[ac]ss$/,
                    use: [extractPlugin, "css-loader", "sass-loader"],
                },
            ],
        },
        plugins: [
            new MiniCssExtractPlugin({
                filename: "mkdocs-jupyter.css",
            }),
        ],
        mode: IS_PRODUCTION ? "production" : "development",
        devtool: "source-map",
    }

    let config = []
    config.push(config_lib)

    return config
}
