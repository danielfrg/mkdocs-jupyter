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
    "styles"
)

module.exports = (env, argv) => {
    const IS_PRODUCTION = argv.mode === "production"

    const config_css = {
        entry: path.resolve(__dirname, "src", "styles.scss"),
        output: {
            path: path.resolve(__dirname, "dist", "styles"),
        },
        module: {
            rules: [
                {
                    test: /\.s?[ac]ss$/,
                    use: [extractPlugin, "css-loader", "sass-loader"],
                },
            ],
        },
        plugins: [
            new FixStyleOnlyEntriesPlugin(),
            new MiniCssExtractPlugin({
                filename: "jupyter-lab.css",
            }),
            // Copy the output to the Python Package
            new FileManagerPlugin({
                events: {
                    onEnd: {
                        copy: [
                            {
                                source: "./dist/styles",
                                destination: pythonPkgStatic,
                            },
                        ],
                    },
                },
            }),
        ],
        optimization: {
            minimize: false,
        },
        // mode: IS_PRODUCTION ? "production" : "development",
        devtool: "source-map",
    }

    let config = []
    config.push(config_css)

    return config
}
