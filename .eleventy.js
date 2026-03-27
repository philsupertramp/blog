const mathjaxPlugin = require("eleventy-plugin-mathjax");
const directoryOutputPlugin = require("@11ty/eleventy-plugin-directory-output");
const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const seoModule = require('./src/utils/seo-module');
const fs = require('fs');

function getLastModified(pageUrl) {
  let path = `./src${pageUrl}`.replace(/.$/, ".md");
  try {
    date = new Date(fs.statSync(path).mtime);
    return date;
  }  catch (err) {
    return new Date();
  }
}

module.exports = function(eleventyConfig) {
    const markdown = require('./src/utils/markdown')
    eleventyConfig.setLibrary('md', markdown.markdown)
    eleventyConfig.addPlugin(syntaxHighlight);

    const { DateTime } = require("luxon");

    eleventyConfig.addFilter("postDate", (dateObj, url) => {
      if (dateObj === 'Last Modified') {
        dateObj = getLastModified(url);
      }
      return DateTime.fromJSDate(dateObj).toLocaleString(DateTime.DATE_MED);
    });
    eleventyConfig.addFilter("notesUrl", (slug) => {
      return `/notes/${slug}/`;
    });
    eleventyConfig.addFilter("postsUrl", (slug) => {
      return `/posts/${slug}/`;
    });

    //
    eleventyConfig.addFilter("getRelatedPosts", function(collection, currentUrl, currentTags) {
      // If the current post has no tags, return nothing
      if (!currentTags || currentTags.length === 0) return [];
      
      // Filter out the current post and posts without matching tags
      const related = collection.filter(post => {
        if (post.url === currentUrl) return false; // Skip the current post
        
        const postTags = post.data.tags || [];
        const excludes = ["post", "note", "published", "old-wiki"];
        excludes.forEach((e) => {
          let idx = postTags.indexOf(e);
          if (idx > -1){
            postTags.splice(idx, 1);
          }
        });
        if (postTags.length <= 0) {
          return false;
        }
        // Check if there is an intersection between the tags
        return currentTags.some(tag => postTags.includes(tag));
      });

      // Return a maximum of 3 related posts
      return related.slice(0, 3);
    }); 

    // ============ SEO FILTERS ============
    eleventyConfig.addFilter("schemaDate", (date, url) => {
      if (date === 'Last Modified') {
        date = getLastModified(url);
      }
      return new Date(date).toISOString();
    });

    eleventyConfig.addFilter("metaDescription", (text, maxLength = 155) => {
      return seoModule.generateMetaDescription(text, maxLength);
    });

    eleventyConfig.addFilter("escapeHtml", (text) => {
      return seoModule.escapeHtml(text);
    });

    eleventyConfig.addFilter("formatDate", (date, url) => {
      if (date === 'Last Modified') {
        date = getLastModified(url);
      }
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
      if(date === 'Last Modified') {
        date = getLastModified(pageUrl);
      }
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

    // some special styles
    eleventyConfig.addShortcode("note", (text) => {
      return `<blockquote class="markdown-alert markdown-alert-note">
        <p class="markdown-alert-title">
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path>
          </svg>
          Note
        </p>
        <p>${text}</p>
      </blockquote>`
    });
    eleventyConfig.addShortcode("caution", (text) => {
      return `<blockquote class="markdown-alert markdown-alert-caution">
        <p class="markdown-alert-title">
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <path d="M4.47.22A.749.749 0 0 1 5 0h6c.199 0 .389.079.53.22l4.25 4.25c.141.14.22.331.22.53v6a.749.749 0 0 1-.22.53l-4.25 4.25A.749.749 0 0 1 11 16H5a.749.749 0 0 1-.53-.22L.22 11.53A.749.749 0 0 1 0 11V5c0-.199.079-.389.22-.53Zm.84 1.28L1.5 5.31v5.38l3.81 3.81h5.38l3.81-3.81V5.31L10.69 1.5ZM8 4a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4Zm0 8a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path>
          </svg>
          Caution
        </p>
        <p>${text}</p>
      </blockquote>`
    });
    eleventyConfig.addShortcode("tip", (text) => {
      return `<blockquote class="markdown-alert markdown-alert-tip">
        <p class="markdown-alert-title">
          <svg viewBox="0 0 16 16" version="1.1" width="16" height="16" aria-hidden="true"><path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.673.848.284.411.537.896.621 1.49a.75.75 0 0 1-1.484.211c-.04-.282-.163-.547-.37-.847a8.456 8.456 0 0 0-.542-.68c-.084-.1-.173-.205-.268-.32C3.201 7.75 2.5 6.766 2.5 5.25 2.5 2.31 4.863 0 8 0s5.5 2.31 5.5 5.25c0 1.516-.701 2.5-1.328 3.259-.095.115-.184.22-.268.319-.207.245-.383.453-.541.681-.208.3-.33.565-.37.847a.751.751 0 0 1-1.485-.212c.084-.593.337-1.078.621-1.489.203-.292.45-.584.673-.848.075-.088.147-.173.213-.253.561-.679.985-1.32.985-2.304 0-2.06-1.637-3.75-4-3.75ZM5.75 12h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1 0-1.5ZM6 15.25a.75.75 0 0 1 .75-.75h2.5a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1-.75-.75Z"></path></svg>
          Tip
        </p>
        <p>${text}</p>
      </blockquote>`
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
      output: 'svg',
      tex: {
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
