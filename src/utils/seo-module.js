/**
 * SEO Module for 11ty
 * Automatically generates BlogPosting schema, meta tags, OG tags, and canonical URLs
 */

const DEFAULT_AUTHOR = 'Philipp';
const SITE_URL = 'https://blog.godesteem.de';
const SITE_NAME = "Phil's Blog";

/**
 * Generate BlogPosting schema (JSON-LD)
 */
function generateBlogPostingSchema(page, post) {
  // Handle both post.data and direct properties
  const data = (post && post.data) || post || {};
  const author_name = data.author || DEFAULT_AUTHOR;
  const {
    title = '',
    description = '',
    date = new Date(),
    tags = []
  } = data;

  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: title,
    description: description || generateMetaDescription(title),
    datePublished: date.toISOString(),
    dateModified: date.toISOString(),
    author: {
      '@type': 'Person',
      name: author_name,
      url: SITE_URL,
      sameAs: [
        "[https://github.com/philsupertramp](https://github.com/philsupertramp)",
        "[https://huggingface.co/philipp-zettl](https://huggingface.co/philipp-zettl)"
      ]
    },
    publisher: {
      '@type': 'Organization',
      name: SITE_NAME,
      url: SITE_URL
    },
    url: `${SITE_URL}${page.url}`,
    image: `${SITE_URL}/_includes/assets/favicon-32x32.png`,
    isPartOf: {
      "@type": "Blog",
      "name": SITE_NAME,
      "publisher": {
        "@type": "Organization",
        "@id": SITE_URL,
        "name": SITE_NAME
      }
    }
  };

  // Add keywords from tags if available
  if (tags && tags.length > 0) {
    const keywords = tags.filter(tag => !['post', 'note', 'published', 'draft'].includes(tag));
    if (keywords.length > 0) {
      schema.keywords = keywords.join(', ');
    }
  }

  return schema;
}

/**
 * Generate Person schema for author
 */
function generatePersonSchema(author = DEFAULT_AUTHOR) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: author,
    url: SITE_URL
  };
}

/**
 * Auto-generate meta description if missing
 * Takes first 155 characters of title/description
 */
function generateMetaDescription(title, description = '') {
  const text = description || title;
  const maxLength = 155;
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).split(' ').slice(0, -1).join(' ') + '...';
}

/**
 * Format date for display (e.g., "Nov 12, 2025")
 */
function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Create canonical URL
 */
function getCanonicalUrl(pageUrl) {
  return `${SITE_URL}${pageUrl}`;
}

/**
 * Get all required meta tags for a page
 */
function getMetaTags(page, post) {
  // Handle both post.data and direct properties
  const data = (post && post.data) || post || {};
  const {
    title = '',
    description = '',
    date = new Date()
  } = data;

  const metaDescription = generateMetaDescription(title, description);
  const canonicalUrl = getCanonicalUrl(page.url);
  const author_name = data.author || DEFAULT_AUTHOR;

  return {
    description: metaDescription,
    canonical: canonicalUrl,
    ogTitle: title,
    ogDescription: metaDescription,
    ogUrl: canonicalUrl,
    ogType: 'article',
    twitterCard: 'summary',
    twitterTitle: title,
    twitterDescription: metaDescription,
    articlePublished: date.toISOString(),
    articleModified: date.toISOString(),
    author: author_name,
  };
}

/**
 * Render all meta tags as HTML strings
 */
function renderMetaTags(page, post) {
  const tags = getMetaTags(page, post);
  
  return {
    description: `<meta name="description" content="${escapeHtml(tags.description)}">`,
    canonical: `<link rel="canonical" href="${tags.canonical}">`,
    ogTitle: `<meta property="og:title" content="${escapeHtml(tags.ogTitle)}">`,
    ogDescription: `<meta property="og:description" content="${escapeHtml(tags.ogDescription)}">`,
    ogUrl: `<meta property="og:url" content="${tags.ogUrl}">`,
    ogType: `<meta property="og:type" content="${tags.ogType}">`,
    ogImage: `<meta property="og:image" content="${SITE_URL}/_includes/assets/favicon-32x32.png">`,
    twitterCard: `<meta name="twitter:card" content="${tags.twitterCard}">`,
    twitterTitle: `<meta name="twitter:title" content="${escapeHtml(tags.twitterTitle)}">`,
    twitterDescription: `<meta name="twitter:description" content="${escapeHtml(tags.twitterDescription)}">`,
    articlePublished: `<meta property="article:published_time" content="${tags.articlePublished}">`,
    articleModified: `<meta property="article:modified_time" content="${tags.articleModified}">`,
    articleAuthor: `<meta property="article:author" content="${tags.author}">`
  };
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Generate full HTML head for SEO (use in your layout)
 */
function renderAllSeoTags(page, post) {
  const metaTags = renderMetaTags(page, post);
  const blogPostingSchema = generateBlogPostingSchema(page, post);
  
  let html = '';
  
  // Add all meta tags
  html += metaTags.description + '\n';
  html += metaTags.canonical + '\n';
  html += metaTags.ogTitle + '\n';
  html += metaTags.ogDescription + '\n';
  html += metaTags.ogUrl + '\n';
  html += metaTags.ogType + '\n';
  html += metaTags.ogImage + '\n';
  html += metaTags.twitterCard + '\n';
  html += metaTags.twitterTitle + '\n';
  html += metaTags.twitterDescription + '\n';
  html += metaTags.articlePublished + '\n';
  html += metaTags.articleModified + '\n';
  html += metaTags.articleAuthor + '\n';
  
  // Add BlogPosting schema
  html += `\n<script type="application/ld+json">\n${JSON.stringify(blogPostingSchema, null, 2)}\n</script>\n`;
  
  return html;
}

module.exports = {
  generateBlogPostingSchema,
  generatePersonSchema,
  generateMetaDescription,
  formatDate,
  getCanonicalUrl,
  getMetaTags,
  renderMetaTags,
  escapeHtml,
  renderAllSeoTags,
  SITE_URL,
  SITE_NAME,
  DEFAULT_AUTHOR
};
