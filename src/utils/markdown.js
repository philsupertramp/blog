const Image = require('@11ty/eleventy-img')
const markdown = require('markdown-it')({
  html: true
});
markdown.renderer.rules.image = function (tokens, idx, options, env, self) {
  function figure(html, caption) {
    return `<figure>${html}<figcaption>${caption}</figcaption></figure>`
  }

  const token = tokens[idx]
  let imgSrc = token.attrGet('src')
  const imgAlt = token.content
  const imgTitle = token.attrGet('title')

  const htmlOpts = { alt: imgAlt, loading: 'lazy', decoding: 'async' }

  if (imgSrc.startsWith('/') && !imgSrc.endsWith('.gif')) {
    imgSrc = imgSrc.replace('/blog/_includes/assets/', 'src/_includes/assets/')
    console.log(imgSrc);
  }
  if (imgSrc.endsWith('.gif')) {
    console.log('Is GIF', imgSrc);
    var imgOut = `<img src="${imgSrc}" alt="${imgAlt}" title="${imgAlt}" width=auto>`

    return figure(imgOut, imgAlt)
  }

  const parsed = (imgTitle || '').match(
    /^(?<skip>@skip(?:\[(?<width>\d+)x(?<height>\d+)\])? ?)?(?:\?\[(?<sizes>.*?)\] ?)?(?<caption>.*)/
  ).groups

  if (parsed.skip || imgSrc.startsWith('http')) {
    const options = { ...htmlOpts }
    if (parsed.sizes) {
      options.sizes = parsed.sizes
    }

    const metadata = { jpeg: [{ url: imgSrc }] }
    if (parsed.width && parsed.height) {
      metadata.jpeg[0].width = parsed.width
      metadata.jpeg[0].height = parsed.height
    }

    const generated = Image.generateHTML(metadata, options)

    if (parsed.caption) {
      return figure(generated, parsed.caption)
    }
    return generated
  }

  const widths = [250, 316, 426, 460, 580, 768]
  const imgOpts = {
    widths: widths
      .concat(widths.map((w) => w * 2)) // generate 2x sizes
      .filter((v, i, s) => s.indexOf(v) === i), // dedupe
    formats: ['webp', 'jpeg', 'png'], // TODO: add avif when support is good enough
    urlPath: '/blog/_include/assets/',
    outputDir: './docs/_include/assets/'
  }

  Image(imgSrc, imgOpts)

  const metadata = Image.statsSync(imgSrc, imgOpts)

  const generated = Image.generateHTML(metadata, {
    sizes: parsed.sizes || '(max-width: 768px) 100vw, 768px',
    ...htmlOpts
  })

  if (parsed.caption) {
    return figure(generated, parsed.caption)
  }
  return generated
}

module.exports = markdown;
