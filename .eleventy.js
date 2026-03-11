const mathjaxPlugin = require("eleventy-plugin-mathjax");
const directoryOutputPlugin = require("@11ty/eleventy-plugin-directory-output");
const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const seoModule = require('./src/utils/seo-module');

module.exports = function(eleventyConfig) {
    const markdown = require('./src/utils/markdown')
    eleventyConfig.setLibrary('md', markdown.markdown)
    eleventyConfig.addPlugin(syntaxHighlight);

    const { DateTime } = require("luxon");

    eleventyConfig.addFilter("postDate", (dateObj) => {
      return DateTime.fromJSDate(dateObj).toLocaleString(DateTime.DATE_MED);
    });
    eleventyConfig.addFilter("notesUrl", (slug) => {
      return `/notes/${slug}/`;
    });

    // ============ SEO FILTERS ============
    eleventyConfig.addFilter("schemaDate", (date) => {
      return new Date(date).toISOString();
    });

    eleventyConfig.addFilter("metaDescription", (text, maxLength = 155) => {
      return seoModule.generateMetaDescription(text, maxLength);
    });

    eleventyConfig.addFilter("escapeHtml", (text) => {
      return seoModule.escapeHtml(text);
    });

    eleventyConfig.addFilter("formatDate", (date) => {
      return seoModule.formatDate(date);
    });

    eleventyConfig.addFilter("canonical", (pageUrl) => {
      return seoModule.getCanonicalUrl(pageUrl);
    });

    // ============ SEO SHORTCODES ============
    eleventyConfig.addShortcode("blogPostingSchema", (page, post) => {
      const schema = seoModule.generateBlogPostingSchema(page, post);
      return `<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`;
    });

    eleventyConfig.addShortcode("personSchema", (author) => {
      const schema = seoModule.generatePersonSchema(author);
      return `<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`;
    });

    eleventyConfig.addShortcode("seoMetaTags", (pageUrl, title, description, author, date) => {
      // Create a post-like object from the individual parameters
      const post = {
        title: title || '',
        description: description || '',
        author: author || 'Philipp',
        date: date || new Date(),
        tags: []
      };
      const page = { url: pageUrl };
      return seoModule.renderAllSeoTags(page, post);
    });

    eleventyConfig.addPassthroughCopy("src/_includes/assets/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/**");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2024-04-14/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2024-05-12/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2025-08-21/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2025-11-12/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2025-12-05/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2025-12-25/*");
    eleventyConfig.addPassthroughCopy("src/_includes/assets/2026-02-01/*");

    eleventyConfig.addPlugin(mathjaxPlugin, {
      tex: {
        processEscapes: false,
      }
    });
    eleventyConfig.addCollection(
		"published",
      function (collectionApi) {
        return collectionApi.getFilteredByTags("published").reverse();
      }
    );
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
    eleventyConfig.addCollection(
      "old_posts",
      function (collectionApi) {
        return collectionApi.getFilteredByTags("old-wiki", "published").reverse().concat(collectionApi.getFilteredByTags('old-blog', 'published').reverse());
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
