const mathjaxPlugin = require("eleventy-plugin-mathjax");
module.exports = function(eleventyConfig) {
    const markdown = require('./src/utils/markdown')
    eleventyConfig.setLibrary('md', markdown)

    const { DateTime } = require("luxon");

    eleventyConfig.addFilter("postDate", (dateObj) => {
      return DateTime.fromJSDate(dateObj).toLocaleString(DateTime.DATE_MED);
    });

    eleventyConfig.addPassthroughCopy("src/_includes/assets/*");

    eleventyConfig.addPlugin(mathjaxPlugin, {
      processEscapes: false,
  });
    return {
        dir: {
            includes: "_includes",
            input: "src",
            output: "docs"
        },
        pathPrefix: "/blog/"
    };
};
