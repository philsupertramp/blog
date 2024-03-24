module.exports = function(eleventyConfig) {

    eleventyConfig.addPassthroughCopy("src/_includes/assets/*");

    return {
        dir: {
            includes: "_includes",
            input: "src",
            output: "docs"
        },
        pathPrefix: "/blog/"
    };
};
