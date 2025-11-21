---
tags:
 - post
 - published
title: Document Processing In The Time of Artificial Intelligence
layout: mylayout.njk
author: Philipp
description: Modern AI models become more and more powerful. In this post we will explore the possibilities when working with documents.
date: 2025-11-12
---

<style>
    /* Use Inter font */
    body {
        font-family: 'Inter', sans-serif;
    }
    /* Custom styles for the PDF "canvas" */
    #pdf-canvas {
        position: relative;
        background-image: linear-gradient(to right, #e5e7eb 1px, transparent 1px), linear-gradient(to bottom, #e5e7eb 1px, transparent 1px);
        background-size: 20px 20px;
        overflow: hidden;
    }
    #pdf-text-output {
        position: absolute;
        font-family: 'Times New Roman', Times, serif; /* Mimic a common PDF font */
        //transform: scaleY(-1); /* PDF coordinates are bottom-left, HTML is top-left */
        transform-origin: bottom left;
        white-space: pre;
    }
    /* Style for clickable code */
    .code-link {
        cursor: pointer;
        text-decoration: underline;
        color: #60a5fa; /* blue-400 */
    }
    .code-link:hover {
        color: #2563eb; /* blue-600 */
    }
    /* Simple modal for explanations */
    #explanation-modal {
        transition: opacity 0.2s ease-in-out;
    }
    table, th, tr, td {
      border: 1px solid black;
      border-collapse: collapse;
      padding: 2px;
    }
    th {
      border: 2px solid black;
    }
    pre[class*="language-"]{
      font-size: 12;
    }
</style>
In this post we want to explore how modern Large Language Models (some people might call them "AI"), like [Google's Gemini](https://deepmind.google/models/gemini/),
are suddenly capable of processing documents of all kinds, not just text.

According to the official docs of Gemini from 2025-11-12 the API currently supports the following media content
- [Image/Video](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Audio](https://ai.google.dev/gemini-api/docs/audio)
- [Document](https://ai.google.dev/gemini-api/docs/document-processing)

You can either provide this content as a URL, via file upload or smaller files directly inside the payload (<20 MB).

Here, we want to focus on the actual Document Processing capabilities of the API and mainly look into handling of different PDF documents.

## PDF Format
Before we can dive deep into the answer to the question how Google's Gemini AI handles document files, we need to discuss what the Portable Document Format (PDF) file format actually is.

Other than text based file formats, like text (`.txt`), CSV (`.csv`), TSV (`.tsv`), JSON (`.json`), YAML (`.yaml`) or TOML (`.toml`) the PDF (`.pdf`) format is a binary format, simiar to ZIP (`.zip` or `.tar.gz`) compressed directories.

PDF is essentially a _container_ that describes a document's layout and content in a way that can be understood by any device that can read the file. This ensures that the document is represented in the same way on any kind of device.

This PDF _container_ contains objects like pages, fonts, images and other metadata, that all get cross-referenced/linked together within a table.

By reading the table and creating relationships between objects we can recreate the document.

Here's an overview of content types we might find inside a PDF file

| Category                  | Examples                                      |
| ------------------------- | --------------------------------------------- |
| **Text content**          | Streams with font references, character codes |
| **Vector graphics**       | Shapes, lines, bezier paths                   |
| **Images**                | Raster data (JPEG, JPEG2000, CCITT, etc.)     |
| **Fonts**                 | Embedded or referenced                        |
| **Metadata**              | Info dict, XMP XML                            |
| **Interactive content**   | Forms, annotations, links                     |
| **Structure / Tags**      | Logical document structure for accessibility  |
| **Embedded attachments**  | PDFs, images, or arbitrary files              |
| **Scripts / Actions**     | JavaScript actions (rare, used in forms)      |

### Interactive Example
Below you can find an interactive example, that allows you to render your PDF file dynamically.
<div>

<style>
/* General page setup for a dark theme, inferred from your code */

/* A simple two-column grid for layout */
.container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: start;
}

/* Styles for the left column */
.controls-column {
    display: flex;
    flex-direction: column;
}

/* Styles for the code textarea */
.pdf-code-textarea {
    width: 100%;
    height: 12rem; /* h-48 */
    padding: 0.5rem; /* p-2 */
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; /* font-mono */
    font-size: 0.875rem; /* text-sm */
    line-height: 1.25rem;
    background-color: rgb(17 24 39); /* bg-gray-900 */
    color: rgb(74 222 128); /* text-green-400 */
    border-radius: 0.375rem; /* rounded-md */
    border: 1px solid rgb(55 65 81); /* border border-gray-700 */
    box-sizing: border-box; /* Ensures padding doesn't affect width */
}

/* Focus state for the textarea */
.pdf-code-textarea:focus {
    outline: none; /* focus:outline-none */
    border-color: rgb(59 130 246); /* focus:ring-blue-500 (simulated) */
    box-shadow: 0 0 0 2px rgb(59 130 246 / 0.5); /* focus:ring-2 (simulated) */
}

/* Styles for the "Run" button */
.run-button {
    margin-top: 1rem; /* mt-4 */
    background-color: rgb(37 99 235); /* bg-blue-600 */
    color: white; /* text-white */
    font-weight: 700; /* font-bold */
    padding: 0.5rem 1rem; /* py-2 px-4 */
    border-radius: 0.5rem; /* rounded-lg */
    width: 100%; /* w-full */
    border: none;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

/* Hover state for the button */
.run-button:hover {
    background-color: rgb(29 78 216); /* hover:bg-blue-700 */
}

/* The sticky sidebar container */
.sticky-sidebar {
    position: sticky;
    top: 2rem; /* top-8 */
}

/* Title for the PDF page */
.pdf-page-title {
    font-size: 1.25rem; /* text-xl */
    line-height: 1.75rem;
    font-weight: 600; /* font-semibold */
    margin-bottom: 0.5rem; /* mb-2 */
}

/* The white paper container */
.pdf-page-container {
    aspect-ratio: 8.5 / 11; /* aspect-[8.5/11] */
    width: 100%; /* w-full */
    background-color: white; /* bg-white */
    border-radius: 0.5rem; /* rounded-lg */
    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1); /* shadow-xl */
    border: 4px solid rgb(209 213 219); /* border-4 border-gray-300 */
    box-sizing: border-box;
}

/* The actual canvas area inside the paper */
.pdf-canvas-area {
    width: 100%; /* w-full */
    height: 100%; /* h-full */
    border-radius: 0.125rem; /* rounded-sm */
    /* This div is where your JS will draw, so it needs position relative
       if you plan to add absolutely positioned elements inside */
    position: relative; 
    overflow: hidden; /* Clips any drawing that goes outside */
}

/* Container for the command log */
.command-log-container {
    margin-top: 1rem; /* mt-4 */
    padding: 1rem; /* p-4 */
    background-color: rgb(31 41 55); /* bg-gray-800 */
    color: white; /* text-white */
    border-radius: 0.5rem; /* rounded-lg */
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); /* shadow-md */
}

/* Title for the command log */
.command-log-title {
    font-weight: 700; /* font-bold */
    margin-bottom: 0.5rem; /* mb-2 */
    margin-top: 0;
}

/* The scrolling log area */
.command-log-area {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; /* font-mono */
    font-size: 0.875rem; /* text-sm */
    line-height: 1.25rem;
    height: 8rem; /* h-32 */
    overflow-y: auto; /* overflow-y-auto */
    color: rgb(74 222 128); /* text-green-400 */
}

/* Responsive layout for smaller screens */
@media (max-width: 768px) {
    .container {
        grid-template-columns: 1fr; /* Stack columns on mobile */
    }
    .sticky-sidebar {
        position: static; /* Don't be sticky on mobile */
    }
}
</style>
  <div class="container">
    <div class="controls-column">
        <p>This is the fun part.</p>
        <p>A PDF doesn't store "Hello World" as you see it. It stores <i>instructions</i> on how to draw it.</p>
        <p>The text below is a "Content Stream". A content stream is the heart of a page. It's a list of drawing commands in a <a href="https://en.wikipedia.org/wiki/PostScript">PostScript</a>-like language.
        <p>You can hack around in the textarea and try out different things to understand the format better.</p>
        <p>For a more detailed description, check out our interactive <a href="/_includes/assets/2025-11-12/interactive-pdf.html">Explainer Page</a>!</p>
        <p><strong>Please note</strong> for demo purposes we only allow you to reference <code>/Img1</code> or <code>/Img2</code>, otherwise we would need to dynamically create the image object inside the document.</p>
        <textarea id="pdf-code" class="pdf-code-textarea">
        </textarea>
        <button id="run-btn" class="run-button">Run Instructions</button>
    </div>
    <div class="sticky-sidebar">
        <h3 class="pdf-page-title">Simulated PDF Page (8.5" x 11")</h3>
        <div class="pdf-page-container">
            <div id="pdf-canvas" class="pdf-canvas-area">
            </div>
        </div>
        <div class="command-log-container">
            <h4 class="command-log-title">Command Log:</h4>
            <div id="command-log" class="command-log-area">
                Click "Run Instructions" to see the log...
            </div>
        </div>
    </div>  
  </div>
  
  <script>
    document.addEventListener('DOMContentLoaded', () => {
        // --- Section 3: Interactive Page Content ---
        const runBtn = document.getElementById('run-btn');
        const codeInput = document.getElementById('pdf-code');
        const canvas = document.getElementById('pdf-canvas');
        const log = document.getElementById('command-log');
        
        codeInput.innerHTML = `BT
/F1 42 Tf
72 750 Td
% Move to position (x:72, y:500)
% (above the image)
(This is a heading!) Tj
ET
q
% q: Save graphics state

200 0 0 150 100 550 cm
% cm: Set transformation matrix
% (scale 200w, 150h; position at x:100, y:550)

/Img1 Do
% Do: Draw the image named /Img1

Q
% Q: Restore graphics state

BT
% Begin Text block

/F1 22 Tf
% Set Font 'F1' to 12 points

72 500 Td
% Move to position (x:72, y:500)
% (below the image)

(Hello, PDF! Images are objects too.) Tj
% Show the text

ET
% End Text block


BT
% Begin Text block

/F1 18 Tf
% Set Font 'F1' to 12 points

72 425 Td
% Move to position (x:72, y:500)
% (below the image)

(We can even reference the same image multiple times, while moving) Tj
% Show the text

70 407 Td
( it around the page.) Tj

ET
% End Text block

q
% q: Save graphics state

200 0 0 150 100 250 cm
% cm: Set transformation matrix
% (scale 200w, 150h; position at x:100, y:550)

/Img1 Do
% Do: Draw the image named /Img1

200 0 0 150 350 250 cm
% cm: Set transformation matrix
% (scale 200w, 150h; position at x:100, y:550)

/Img2 Do
% Do: Draw the image named /Img2

Q
% Q: Restore graphics state`;

        runBtn.addEventListener('click', () => {
            // Clear previous run
            canvas.innerHTML = '';
            log.innerHTML = '';

            const lines = codeInput.value.split('\n');
            
            let graphicsState = {
                font: '12px',
                textMatrix: [1, 0, 0, 1, 0, 0], // For Td
                currentMatrix: null // For cm
            };
            let stateStack = [];
            let inTextObject = false;

            // Dimensions of a US Letter page in points (612x792)
            const pageHeight = 792;
            
            // Canvas dimensions (for scaling)
            const canvasHeight = canvas.clientHeight;
            const canvasWidth = canvas.clientWidth;
            
            // PDF y-coords are from bottom, HTML y-coords are from top.
            // We need to flip them.
            const scale = canvasHeight / pageHeight;

            lines.forEach((line, index) => {
                // Trim whitespace and comments
                let command = line.split('%')[0].trim();
                if (!command) {
                    if (line.trim().startsWith('%')) {
                        logMessage(`Comment: ${line.trim().substring(1)}`, 'gray');
                    }
                    return; // Skip empty lines or full-line comments
                }

                const parts = command.split(' ');
                const operator = parts.pop();

                switch (operator) {
                    case 'q':
                        stateStack.push(JSON.parse(JSON.stringify(graphicsState)));
                        logMessage('q: Save Graphics State', 'blue');
                        break;
                    case 'Q':
                        if (stateStack.length > 0) {
                            graphicsState = stateStack.pop();
                            logMessage('Q: Restore Graphics State', 'blue');
                        } else {
                            logMessage('Error: Unmatched Q', 'red');
                        }
                        break;
                    case 'BT':
                        inTextObject = true;
                        graphicsState.textMatrix = [1, 0, 0, 1, 0, 0]; // Reset text matrix
                        logMessage('BT: Begin Text Block', 'blue');
                        break;
                    case 'ET':
                        inTextObject = false;
                        logMessage('ET: End Text Block', 'blue');
                        break;
                    case 'Tf':
                        const fontSize = parts.pop();
                        const fontName = parts.join(' ');
                        graphicsState.font = `${fontSize}px`;
                        logMessage(`Tf: Set Font ${fontName} to ${fontSize}pt`, 'green');
                        break;
                    case 'Td':
                        const y = parseFloat(parts.pop());
                        const x = parseFloat(parts.pop());
                        graphicsState.textMatrix = [1, 0, 0, 1, x, y];
                        logMessage(`Td: Move to (x:${x}, y:${y})`, 'green');
                        break;
                    case 'Tj':
                        if (inTextObject) {
                            const text = command.substring(command.indexOf('(') + 1, command.lastIndexOf(')'));
                            logMessage(`Tj: Show Text "${text}"`, 'yellow');
                            
                            // Create and position the text element
                            const textEl = document.createElement('div');
                            textEl.id = 'pdf-text-output';
                            textEl.textContent = text;
                            
                            // Get position from text matrix
                            const currentX = graphicsState.textMatrix[4];
                            const currentY = graphicsState.textMatrix[5];

                            // Scale positions to fit our canvas
                            const scaledX = currentX * scale;
                            
                            // Calculate 'top' position for HTML
                            // (pageHeight - currentY) gives the Y-coord from the top in PDF points
                            // Then we scale it to the canvas size
                            const htmlTop = (pageHeight - currentY) * scale;
                            const scaledFontSize = parseFloat(graphicsState.font) * scale;

                            textEl.style.fontSize = `${scaledFontSize}px`;
                            textEl.style.left = `${scaledX}px`;
                            // PDF's (x,y) is the bottom-left of the text.
                            // HTML's (left,top) is the top-left of the div.
                            // We subtract font size to align the baselines correctly.
                            textEl.style.top = `${htmlTop - scaledFontSize}px`; 
                            
                            canvas.appendChild(textEl);
                        } else {
                            logMessage('Error: Tj operator outside BT/ET block', 'red');
                        }
                        break;
                    case 'cm':
                        const matrix = parts.map(parseFloat);
                        if (matrix.length === 6) {
                            graphicsState.currentMatrix = matrix;
                            logMessage(`cm: Set Matrix [${matrix.join(' ')}]`, 'green');
                        } else {
                            logMessage(`Error: Invalid cm operator`, 'red');
                        }
                        break;
                    case 'Do':
                        const imageName = parts.join(' ');
                        logMessage(`Do: Draw Object ${imageName}`, 'yellow');
                        
                        if (graphicsState.currentMatrix) {
                            const [a, b, c, d, e, f] = graphicsState.currentMatrix;
                            let img_path = (imageName === '/Img1' ? '/_includes/assets/newton.jpg' : '/_includes/assets/collage-cat.jpg');
                            console.log(img_path, imageName)
                            
                            const imgPlaceholder = document.createElement('div');
                            imgPlaceholder.style.cssText = `
                                background: center url(` + img_path + `);
                                background-size: contain;
                                position: absolute;
                                border: 2px dashed #9ca3af;
                                color: #6b7280;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-family: 'Inter', sans-serif;
                                font-size: 14px;
                                box-sizing: border-box;
                            `;
                            
                            const width = a * scale;
                            const height = d * scale;
                            const x = e * scale;
                            const y_pdf = f; // PDF y-coord
                            
                            // HTML top is calculated from PDF's bottom-left y
                            const htmlTop = (pageHeight - y_pdf) * scale - height;
                            
                            imgPlaceholder.style.width = `${width}px`;
                            imgPlaceholder.style.height = `${height}px`;
                            imgPlaceholder.style.left = `${x}px`;
                            imgPlaceholder.style.top = `${htmlTop}px`;
                            
                            canvas.appendChild(imgPlaceholder);
                        } else {
                            logMessage('Error: "Do" without preceding "cm" matrix', 'red');
                        }
                        break;
                    default:
                        logMessage(`Unknown op: ${command}`, 'gray');
                }
            });
        });

        function logMessage(message, color) {
            const colors = {
                'blue': 'text-blue-400',
                'green': 'text-green-400',
                'yellow': 'text-yellow-400',
                'red': 'text-red-500',
                'gray': 'text-gray-500'
            };
            log.innerHTML += `<span class="${colors[color] || 'text-white'} block">&gt; ${message}</span><br/>`;
            log.scrollTop = log.scrollHeight; // Auto-scroll
        }
        
        // Initial run to show something
        runBtn.click();
    });
    
  </script>
</div>


## Real life examples
Let's also look into actual real life cases.

Consider these two very similar documents, both only contain the string "Hello World".

The left document was created with Google Docs, the right one with ["LaTeX"](https://en.wikipedia.org/wiki/LaTeX).

<!--
Source - https://stackoverflow.com/a/7044015
Posted by Batfan, modified by community. See post 'Timeline' for change history
Retrieved 2025-11-12, License - CC BY-SA 4.0
-->
<div style="display: flex">
  <div style="width: 45%; margin-right: 5%">
    <embed src="/_includes/assets/2025-11-12/test-doc-2.pdf" width="100%" height="100%" type="application/pdf">
  </div>
  <div style="width: 45%">
    <embed src="/_includes/assets/2025-11-12/test-doc-3.pdf" width="100%" height="100%" type="application/pdf">
  </div>
</div>

Sure, the font is a bit different and the placement of the text content itself is also a little different, but that should be it, right?

<b>No</b>.

Once we look at the binary data of the document, it gets more and more confusing and the difference get bigger and bigger the more we look at the content.

So what's the deal?

<div>
  <div class="command-log-container">
    <h4 class="command-log-title">Google Docs Document</h4>
    <div class="fileContent command-log-area" id="file-1-output"></div>
  </div>
  <div class="command-log-container">
    <h4 class="command-log-title">LaTeX Document</h4>
    <div class="fileContent command-log-area" id="file-2-output"></div>
  </div>
<script>
// Source - https://stackoverflow.com/a/29176118
// Posted by Amit Chaurasia, modified by community. See post 'Timeline' for change history
// Retrieved 2025-11-12, License - CC BY-SA 4.0
var openFile = async function(target, element) {
  var input = target;
  var reader = new FileReader();
  reader.onload = function() {
    var text = reader.result;
    element.innerText = text;
  };
  let data = await fetch(target).then(r => r.blob());
  console.log(data);
  reader.readAsText(data);
};
openFile('/_includes/assets/2025-11-12/test-pdf-2.txt', document.getElementById("file-1-output"))
openFile('/_includes/assets/2025-11-12/test-pdf-3.txt', document.getElementById("file-2-output"))
</script>
</div>

As you can see we get already the first difference in the PDF file version number (the first line).
For Google's PDF we get <code>PDF-1.4</code> and for the LaTeX doc it is <code>PDF-1.5</code>.

Due to the fact that PDF is by now an industry standard, the versions are also tagged with ISO numbers. The most recent PDF version (PDF 2.0) has the ISO ID <code>ISO 32000-2:2020</code>. And if you're curious about it, you can buy yourself a PDF version of the PDF version on <a href="www.iso.org/standard/75839.html">iso.org<a> (for _just_ 221 CHF).

> Kinda funny that you can buy a PDF document about the PDF format


Now if you look a little more into both generated documents, you will notice that albeit both spell "Hello World", none of them actually contain the combined letters spelling it out.

### Further investigation

We can use UNIX tools to investigate this a little further.
In the following, the Google PDF is called `test-doc-2.pdf` and the LaTeX doc is called `test-doc-3.pdf`.

For instance `pdfinfo` gives us some information about the files.

First the Google Doc
```
> pdfinfo ./test-doc-2.pdf
Title:           Untitled document
Producer:        Skia/PDF m144 Google Docs Renderer
Custom Metadata: no
Metadata Stream: no
Tagged:          yes
UserProperties:  no
Suspects:        no
Form:            none
JavaScript:      no
Pages:           1
Encrypted:       no
Page size:       596 x 842 pts (A4)
Page rot:        0
File size:       11688 bytes
Optimized:       no
PDF version:     1.4
```
And then the LaTeX doc
```
> pdfinfo ./test-doc-3.pdf
Creator:         TeX
Producer:        pdfTeX-1.40.27
CreationDate:    Wed Nov 12 13:55:15 2025 CET
ModDate:         Wed Nov 12 13:55:15 2025 CET
Custom Metadata: yes
Metadata Stream: no
Tagged:          no
UserProperties:  no
Suspects:        no
Form:            none
JavaScript:      no
Pages:           1
Encrypted:       no
Page size:       612 x 792 pts (letter)
Page rot:        0
File size:       13141 bytes
Optimized:       yes
PDF version:     1.5
```

Using `qpdf` we can create a more readable PDF without object streams and compression
```
> qpdf -qdf --object-streams=disable ./test-doc-2.pdf ./test-doc-2.qdf.pdf
> qpdf -qdf --object-streams=disable ./test-doc-3.pdf ./test-doc-3.qdf.pdf
```
This produces the following two documents
<div style="display: flex">
  <div style="width: 45%; margin-right: 5%">
    <embed src="/_includes/assets/2025-11-12/test-doc-2.qdf.pdf" width="100%" height="100%" type="application/pdf">
  </div>
  <div style="width: 45%">
    <embed src="/_includes/assets/2025-11-12/test-doc-3.qdf.pdf" width="100%" height="100%" type="application/pdf">
  </div>
</div>

Again, they look exactly the same inside the reader, but they're a bit more readable because nothing is compressed or streamed.

Once we look over the document's content, we can see blocks
```
BT
...
ET
```
which are our text boxes (`BT`: Begin Text, `ET`: End Text), and
```
begincmap
...
endcmap
```
which defines our character map for the document.

Doing some Python Kong-Fu allows us to read this data, and re-create the document content. It's not too trivial, but I'm sure you'll understand the gist of it.

We start with creating the character map
```python
import re

def parse_to_unicode_cmap(cmap_text: str) -> dict[str, str]:
    """
    Parse a single begincmap...endcmap text and return a dict mapping
    keys like '<002b>' -> 'H'.
    """
    cmap = {}
    BF_RANGE_BLOCK = r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>\s+\[(.*?)\]"
    FRANGE_BLOCK = r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>"
    
    FRANGE = r"beginbfrange(.*?)endbfrange"
    FCHAR = r"beginbfchar(.*?)endbfchar"
    FCHAR_BLOCK = r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>"
    

    # beginbfchar ... endbfchar
    for bfchar_block in re.finditer(FCHAR, cmap_text, re.S | re.I):
        block = bfchar_block.group(1)
        for src, dst in re.findall(FCHAR_BLOCK, block):
            key = f"<{int(src,16):04x}>"   # normalized "<xxxx>"
            cmap[key] = chr(int(dst, 16))

    # beginbfrange ... endbfrange
    for bfrange_block in re.finditer(FRANGE, cmap_text, re.S | re.I):
        block = bfrange_block.group(1)
        # three-hex form: <start> <end> <dst_start>
        for start, end, dst in re.findall(FRANGE_BLOCK, block):
            s, e, d = int(start, 16), int(end, 16), int(dst, 16)
            for offset, codepoint in enumerate(range(s, e + 1)):
                key = f"<{codepoint:04x}>"
                cmap[key] = chr(d + offset)

        # alternative bfrange form where destination is an array
        # e.g. <start> <end> [ <dst1> <dst2> ... ]
        for start, end, arr in re.findall(BF_RANGE_BLOCK, block, re.S):
            s, e = int(start, 16), int(end, 16)
            dsts = re.findall(r"<([0-9A-Fa-f]+)>", arr)
            for i, codepoint in enumerate(range(s, e + 1)):
                if i < len(dsts):
                    key = f"<{codepoint:04x}>"
                    cmap[key] = chr(int(dsts[i], 16))

    return cmap
```
The explanation is quite simple.
We have two major blocks we consider as definitions of our character map.
One is wrapped between `beginfchar...endfchar`, the other between `beginbfrange...endbfrange`.

`FCHAR` is a conversion pair with `SOURCE` and `DESTINATION`, e.g.

```text
beginbfchar
<0000> <0049>
endbfchar
```
This maps for example the code `<0000>` to the character `I`.

The other block type `bfrange` contains 3 elements per record `start`, `end`, `destination`, e.g.
```text
beginbfrange
<0000> <0010> <0049>
endbfrange
```
This essentially maps the codes `<0000>, <0001>, ..., <0010>` to the character `I`.

Our method will iterate over every line of each block and create the character map based on these definitions.

<u>One thing to mention, tho, if we have elements inside `bfrange` blocks that were present in the previous `bfchar` block we will overwrite them with the range content.</u>

But we don't have immediately the character map content, rather the whole document.

With the following method we can extract the definition
```python
def build_global_map_from_pdf_text(data: str) -> dict[str, str]:
    maps = {}
    for cmap_match in re.finditer(r"begincmap(.*?)endcmap", data, re.S | re.I):
        mapping = parse_to_unicode_cmap(cmap_match.group(1))
        # Later ones may override earlier ones for the same code — that's okay
        maps.update(mapping)
    return maps
```

Progressing further, apart from the character map we also need the text blocks. As previously mentioned, they're indicated by `BT...ET` blocks. We can yet again use our always helpful helper RegEx

```python
def decode_bt_block(block_text: str, maps: dict[str, str]) -> str:
    """
    Finds hex tokens <hhhh> inside the block and decodes using maps,
    falling back to '?' when unknown.
    """
    out = []
    for m in re.finditer(r"<([0-9A-Fa-f]+)>", block_text):
        # hex representation with width 4 and prefixed 0
        key = f"<{int(m.group(1), 16):04x}>"
        out.append(maps.get(key, "?"))
    return "".join(out)
```

And finally wrapping up to just require the document binary data we can wrap everything into this neat little method
```python
def extract_text_from_uncompressed_pdf(data: str) -> None:
    maps = build_global_map_from_pdf_text(data)
    content = []
    for block in re.finditer(r"BT(.*?)ET", data, re.S):
        decoded = decode_bt_block(block.group(1), maps)
        # you may also want to print raw block for debugging
        print(decoded)
        content.append(decoded)
    return content
```

Feel free to use one of the converted PDF files from earlier `https://blog.godesteem.de/_includes/assets/2025-11-12/test-doc-2.qdf.pdf`, e.g.
```python
import requests

url = 'https://blog.godesteem.de/_includes/assets/2025-11-12/test-doc-2.qdf.pdf'
data = extract_text_from_uncompressed_pdf(requests.get(url, allow_redirects=True).content)
```
and that will yield
```text
Hello
 
World
```

Woohoo, congrats! We managed to extract text content from our document(s)!

<iframe src="https://giphy.com/embed/zQ59i1AwVXhd2chKyX" width="auto" height="250px" frameBorder="0" class="giphy-embed" allowFullScreen></iframe>


Alright, that's not fully usable for us, just yet.
What we would actually want is apart from the text content also a form of structure, like bounding boxes or coordinates.

### Structure Parsing

Thankfully, the PDF got us covered.
We can use the `BT..ET` blocks to retrieve this information.
Inside each block we have a set of instructions that help us structure the content.
These instructions include

| Operator          | Meaning                                                 |
| ----------------- | ------------------------------------------------------- |
| `Tm`              | Set text matrix (scaling + rotation + initial position) |
| `Td`              | Move text position (relative offset in text space)      |
| `Td` + `Tj` chain | Position, draw text, move cursor                        |
| `TJ`              | Basically like `Td` + `Tj` for a single element         |
| `T*`              | Move to next line                                       |
| `Tf`              | Set font and size (you can derive line height)          |


Next in line would be recreating text sturcture, so apart from our text content, we also need to retrieve the position of each text element.

**Note**: That being said, the approach we're looking into here will only work well for documents that have horizontal text on the same line.
Otherwise we will need to come up with a more sophisticated algorithm that will be beyond this post.

Great, now let's get started and extract coordinates for text!

First, we need to extend our `extract_text_from_uncompressed_pdf` method, to not only consider the `BT..ET` blocks, but also their prepending movement instruction that is indicated by the line ending `cm`. These blocks are page level coordinate transformations for all content that follows them.
This will allow us to extract all text content as well as create transformation matrices to move the content inside the document according to the structure defined inside the PDF.


```python
def extract_text_from_uncompressed_pdf(data: str) -> list:
    cmap = build_global_map_from_pdf_text(data)
    CMD_RE = re.compile(
        r"(\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+cm)"  # 1: ...cm
        r"|(BT(.*?)ET)",                             # 2: BT...ET
        re.S
    )

    identity_matrix = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    ctm = list(identity_matrix) # Page-level Matrix
    tm = list(identity_matrix)  # Text Matrix
    tlm = list(identity_matrix) # Text-Line Matrix
    font = None
    # just a default font size, will be extracted from the PDF
    size = 12.0

    all_text_items = []
    for m in CMD_RE.finditer(data):
        cm_match = m.group(1)
        bt_content = m.group(3)
        if cm_match:
            ctm = [float(v) for v in cm_match.split()[:6]]
            continue
        if bt_content is None:
            continue

        try:
            items, tm, tlm, size, font = decode_bt_block(
                bt_content, cmap, ctm, tm, tlm, size, font
            )
            if items:
                all_text_items.append(items)
        except (ValueError, IndexError):
            continue
    return all_text_items

```
<a name="math-example"></a>
As you can see we're using a bit more advanced RegEx now.
It essentially looks for two types of content
First the lines ending with
```
...cm
```
second, the content wrapped inside `BT..ET` tags.

In our test document this could be
```
 .75 0 0 .75 77.25 232.02759 cm
```
and
```
 
/F4 14.666667 Tf
1 0 0 -1 0 .47981739 Tm
88.774796 -13.2773438 Td <0049> Tj
4.0719757 0 Td <0052> Tj
8.1511078 0 Td <0051> Tj
8.1511078 0 Td <0057> Tj
```
We described the specific `BT` block attributes already in the table above.
The `cm` blocks contain 6 float values followed by a `cm`, basically like the `Tm` blocks inside `BT` blocks. But instead of a local transformation it contains a global one.
The first 4 values is the scaling matrix of the content
\begin{pmatrix}
x_{0,0} & x_{1,0}\\\\
x_{0,1} & x_{1,1}
\end{pmatrix}

and the last two are the page coordinates to which to move

\begin{pmatrix}
  \Delta_x\\\\
  \Delta_y
\end{pmatrix}

This allows us to compute coordinates simply by doing


\begin{align}
\begin{pmatrix}
x_{\text{new}}\\\\y_{\text{new}}
\end{pmatrix} = 
\begin{pmatrix}
x_{0,0} & x_{1,0}\\\\
x_{0,1} & x_{1,1}
\end{pmatrix}
\cdot 
\begin{pmatrix}
x\\\\y
\end{pmatrix}
+ 
\begin{pmatrix}
  \Delta_x\\\\
  \Delta_y
\end{pmatrix}
\end{align}

Let's assume we have the starting coordinates `[50, 20]`

\begin{align}
\begin{pmatrix}
x_{\text{new}}\\\\y_{\text{new}}
\end{pmatrix} = 
\begin{pmatrix}
0.75 & 0\\\\
0 & 0.75
\end{pmatrix}
\cdot 
\begin{pmatrix}
50\\\\20
\end{pmatrix}
+ 
\begin{pmatrix}
  77.25\\\\
  232.02759
\end{pmatrix} =
\begin{pmatrix}
  114.75\\\\
  247.02759
\end{pmatrix}
\end{align}

Great, this allows us now to properly extract bounding boxes of our text.

All we need to do is adjust our `decode_bt_block` method. Instead of strings, it will now return a list of structured elements with the form
```json
{
  "text": "Hello World",
  "x": 0,
  "y": 0,
  "size": 12,
  "bbox": [0, 0, 25.5, 12]
}
```
This will be a bit more work now, because instead of just the reading all `<hhhh>` hex tokens, we now need to parse all different attributes to properly understand the structure.

For this we extend our simple `Tj` RegEx with definitions for `Tm`, `Td`, `Tf` and `TJ`

```python
BT_CMD_RE = re.compile(
    r"(\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+Tm)"  # 1: Tm
    r"|(\S+\s+\S+\s+Td)"                         # 2: Td
    r"|(\S+\s+\S+\s+Tf)"                         # 3: Tf
    r"|<([0-9A-Fa-f]+)>\s*Tj"                    # 4: Tj (simple)
    r"|\[(.*?)\]\s*TJ"                           # 5: TJ (with positioning)
)
```
This yields the following 6 groups
- `Tm`: gives us 6 float values
- `Td`: 2 float values
- `Tf`: 2 float values
- `Tj`: hex token value (`<hhhh>` hex token without brackets -> `hhhh`)
- `TJ` a list of elements, each are of form `<hhhh> ... ...`

For now and for the sake of simplicity we ignore the `TJ` blocks here, but you should definitely look into them!

```python
def decode_bt_block(block_content: str, cmap: dict[str, str], ctm: list[float], tm: list[float], tlm: list[float], size: float, font_name: str = None):
    items = []
    
    local_tm = list(tm)
    local_tlm = list(tlm)
    local_size = size
    local_font = font_name

    for m in BT_CMD_RE.finditer(block_content):
        ...
```
Because we're iterating over all `BT..ET` blocks, we need to keep track of the transformations. Hence, our method gets the global Page level, Text level and Text-Line level matrices as input.
Apart from that we pass the current font size and font name to the method, just for simplicities sake.

Like with the simple hex token extraction we iterate over the groups we find inside the provided text block.

Now, let's look inside this loop and see how we parse the content.


```python
for m in BT_CMD_RE.finditer(block_content):
    tm_match = m.group(1)
    td_match = m.group(2)
    tf_match = m.group(3)
    tj_match = m.group(4)
    TJ_match = m.group(5)  # TODO: implement me 
    
    try:
        if tm_match:
            vals = [float(v) for v in tm_match.split()[:6]]
            local_tm = vals
            local_tlm = vals
        
        elif td_match:
            dx, dy = map(float, td_match.split()[:2])
            move_matrix = [1.0, 0.0, 0.0, 1.0, dx, dy]
            local_tlm = matrix_multiply(move_matrix, local_tlm)
            local_tm = list(local_tlm)
            
        elif tf_match:
            parts = tf_match.split()
            local_font = parts[0].strip("/")
            local_size = float(parts[1])
            
        elif tj_match:
            hex_str = tj_match.lower()
            
            for i in range(0, len(hex_str), 4):
                code_hex = hex_str[i:i+4]
                code = f"<{int(code_hex, 16):04x}>" 
                text = cmap.get(code, "?")

                # This should use some more advanced heuristics
                # to properly convert spacing
                w_text_space = local_size 

                final_matrix = matrix_multiply(local_tm, ctm)
                (tx, ty) = transform_point(0, 0, final_matrix)

                w_page_simple = w_text_space * final_matrix[0]
                h_page_simple = local_size * final_matrix[3]
                bbox = (tx, ty, tx + w_page_simple, ty + h_page_simple)
                
                items.append(dict(
                    text=text, 
                    x=tx, 
                    y=ty, 
                    size=local_size * 0.5,
                    bbox=bbox
                ))
                
                advance_matrix = [1, 0, 0, 1, w_text_space, 0]
                local_tm = matrix_multiply(advance_matrix, local_tm)
```

As you can see we're using two helper methods `transform_point` and `matrix_multiply`.
Those are quite literal just matrix-vector operators. I didn't want to integrate the next dependency, just to do some simple math.

Here are the two methods
```python
def matrix_multiply(M1, M2):
    """Performs PDF matrix multiplication: M = M1 * M2"""
    a1, b1, c1, d1, e1, f1 = M1
    a2, b2, c2, d2, e2, f2 = M2
    
    a = a1*a2 + b1*c2
    b = a1*b2 + b1*d2
    c = c1*a2 + d1*c2
    d = c1*b2 + d1*d2
    e = e1*a2 + f1*c2 + e2
    f = e1*b2 + f1*d2 + f2
    
    return [a, b, c, d, e, f]

def transform_point(x, y, M):
    """Transforms a point (x, y) by a matrix M."""
    a, b, c, d, e, f = M
    tx = x*a + y*c + e
    ty = x*b + y*d + f
    return tx, ty
```

It's simple rendering math. You have local coordinates of an object you want to render onto your screen.
But your screen only knows global (world) coordinates.
So to overcome this we "translate" the local matrix into world space, then compute new coordinates according to new world space. Just like we did in the [example](#math-example) before.

Let's consider a different doc that is a bit more complex.

<div style="display: flex">
  <div style="width: 95%; height: 250px; margin-right: 5%">
    <embed src="/_includes/assets/2025-11-12/green-on-green.qdf.pdf" width="100%" height="100%" type="application/pdf">
  </div>
</div>

Using this adjusted implementation we can now recreate the document structure as desired.

<div style="display: flex">
  <div style="width: 45%; margin-right: 5%">
     <img src="/_includes/assets/2025-11-12/test-doc.png" />
  </div>
  <div style="margin-left: 5%; width: 45%">
    Here you can see the text content that make up the full document, as well as the table that contains text inside the document.
    Apart from that you can see that we're able to extract all text, even the one underneath the image that is green text on green background.
    But we still don't actually detect tables, nor images inside the document.
  </div>
</div>
Vector graphics will be the last bit we'll tackle manually, then we'll move onto bigger things, with a more reliable backend.

### Vector Graphic Parsing
Vector graphics are quite similar to images, with the major difference of how they're encoded into the document. We differentiate between `rect` elements, which are rectangles and `line` elements which are just lines.

```python
def find_vectors(data: str) -> list:
    """Finds simple rectangles and lines."""
    vectors = []
    for m in re.finditer(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+re", data):
        x, y, w, h = map(float, m.groups())
        vectors.append({
            "type": "rect",
            "bbox": [x, y, x + w, y + h]
        })
    
    for m in re.finditer(r"(\S+)\s+(\S+)\s+m\s+(\S+)\s+(\S+)\s+l\s+S", data):
        x1, y1, x2, y2 = map(float, m.groups())
        vectors.append({
            "type": "line",
            "p1": [x1, y1],
            "p2": [x2, y2]
        })
            
    return vectors
```
This helps us drastically to identify tables, as well as images inside PDFs.
<div style="display: flex">
  <div style="width: 45%; margin-right: 5%">
    Comparing this rendered document with the previous one make it quite obvious how the vector graphics inside the doc help us recreate the structure.<br/>
    As you can see we can already identify all elements on the page.
    The outer bounding box represents the full document, the lines and columns in the middle of the page represent the table and the box overlapping with the documents center we have the image.
  </div>
  <div style="margin-left: 5%; width: 45%">
     <img src="/_includes/assets/2025-11-12/test-vecs.png" />
  </div>
</div>


Great, this gives us an amazing base to start off. But unfortunately, things get harder and harder from here on.

Our full script is getting bigger and bigger and accumulates more and more dependencies.
Considering this, and the fact that we currently still need to decompress the incoming PDF files as initially mentioned using `qpdf`, we will now pivot to a more robust solution.

## Existing solutions
There's not yet a single library that claims to do exactly what we're doing here.

Hence, we still need to put in some effort to end up with a solid solution.

A brief research on the most commonly used libraries concluded that we should probably use one of these:
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF): *a high performance Python library for data extraction, analysis, conversion & manipulation of PDF (and other) documents*
- [pdfplumber](https://github.com/jsvine/pdfplumber): *Plumb a PDF for detailed information about each char, rectangle, line, et cetera — and easily extract text and tables*
- [Unstructured](https://github.com/Unstructured-IO/unstructured): *Convert documents to structured data effortlessly. Unstructured is open-source ETL solution for transforming complex documents into clean, structured formats for language models. Visit our website to learn more about our enterprise grade Platform product for production grade workflows, partitioning, enrichments, chunking and embedding.*

| Feature          | PyMuPDF (fitz)                        | pdfplumber                             | Unstructured            |
|------------------|---------------------------------------|----------------------------------------|-------------------------|
| Text Extraction  | Excellent (C-Speed, Dict/JSON output) | Excellent (Visual/Layout preservation) | Good (OCR/Partitioning) |
| Table Extraction | Good (Fast, Heuristic)                | Excellent (Configurable, Visual Debug) | Good (Auto-detection)   |
| Vector Graphics  | Full Support (Paths to SVG)           | Limited (Lines/Rects only)             | Limited (Rasterizes)    |
| Raster Images    | Native Extraction                     | Native Extraction                      | Native (OCR capable)    |
| Output Format    | Dict, JSON, XML, Markdown             | JSON/CSV export                        | JSON (Element list)     |
| Execution Speed  | 🚀 Very Fast (~0.1s/page)             | 🐢 Slow (~1-5s/page)                   | 🐢 Slow (~1.5s+/page)   |
| License          | AGPL (Restrictive) / Commercial       | MIT (Permissive)                       | Apache 2.0 (Permissive) |

We decided for now to go with [PyMuPDF](https://github.com/pymupdf/PyMuPDF) due to its performance.


We migth later take a look at PDFPlumber for table extraction, but that's an optimization for another day.
