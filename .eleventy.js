const mathjaxPlugin = require("eleventy-plugin-mathjax");
const directoryOutputPlugin = require("@11ty/eleventy-plugin-directory-output");
const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");

module.exports = function(eleventyConfig) {
    const markdown = require('./src/utils/markdown')
    eleventyConfig.setLibrary('md', markdown)
    eleventyConfig.addPlugin(syntaxHighlight);

    const { DateTime } = require("luxon");

    eleventyConfig.addFilter("postDate", (dateObj) => {
      return DateTime.fromJSDate(dateObj).toLocaleString(DateTime.DATE_MED);
    });
    eleventyConfig.addFilter("notesUrl", (slug) => {
      return `/notes/${slug}/`;
    });

    eleventyConfig.addPassthroughCopy("src/_includes/assets/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2024-04-14/*");

    eleventyConfig.addPlugin(mathjaxPlugin, {
      processEscapes: false,
  });

	eleventyConfig.addCollection(
		"published_notes",
		function (collectionApi) {
			return collectionApi.getFilteredByTags("note", "published").reverse();
		}
	);
	eleventyConfig.addCollection(
		"published_posts",
		function (collectionApi) {
			return collectionApi.getFilteredByTags("post", "published").reverse();
		}
	);

  
	eleventyConfig.addPlugin(directoryOutputPlugin, {
		// Customize columns
		columns: {
			filesize: true, // Use `false` to disable
			benchmark: true, // Use `false` to disable
		},

		// Will show in yellow if greater than this number of bytes
		warningFileSize: 400 * 1000,
	});
    return {
        dir: {
            includes: "_includes",
            input: "src",
            output: "docs"
        },
        pathPrefix: ""
    };
};
