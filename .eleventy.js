const mathjaxPlugin = require("eleventy-plugin-mathjax");

module.exports = function(eleventyConfig) {

    eleventyConfig.addPassthroughCopy("src/_includes/assets/*");

    eleventyConfig.addPlugin(mathjaxPlugin);
    return {
        dir: {
            includes: "_includes",
            input: "src",
            output: "docs"
        },
        pathPrefix: "/blog/"
    };
};
