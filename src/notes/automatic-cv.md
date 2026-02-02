---
tags:
 - note
 - published
title: "Automatic CV building"
layout: mylayout.njk
author: Philipp
description: Building CVs using LaTeX, automatically, in the cloud using config files for content
date: 2026-02-01
---

I'm currently in the process of looking for a new job. Last time I was in this situation was in mid 2018.
But instead of searching for another Working Student position, like back then, this time I seek full time employment.
Hence, instead of a makeshift Word Doc with a one liner introduction and a three column table with duration, job title and employer,
I need something more professional.

During my studies I grew fond of LaTeX

> LaTeX is a widely-used, free document preparation system designed for high-quality typesetting, specializing in technical and scientific, formula-heavy documentation
. It operates as a markup language, separating content from design, where users write code that is compiled into formatted PDFs.

Which is perfect for my plan.

In this post/note today, we will write a quick template that we can fill with source files and then build our nicely looking, **constistently styled** curriculum vitae.

## Quick LaTeX intro

One thing up-front, you're gonna be way better off looking into a tutorial/guide around LaTeX. The platform [overleaf](https://overleaf.org) is a great and rich resource for that.
For instance [here](https://docs.overleaf.com/getting-started/latex-tutorials).

We can code LaTeX documents in our text editors and then build/compile/render them using a command line tool-chain.

Some of these tool chains are pdfTeX, XeTeX or LuaTeX.

The whole build process is quite complicated.
We'll focus on two tools today, pdfTeX and BibTeX.
Actually, we'll be using [philsupertramp/tex-starter](https://github.com/philsupertramp/tex-starter), a pre-built pipeline for all of my LaTeX documents.

pdfTeX will handle layout and content rendering for us, whereas BibTex takes care of references.
We will most likely not use BibTeX in our CV, but I use it mostly to have a consistent build process accross all my documents.

Alright, without any further ado here's a quick example of an article document.


<style>
  .responsive-container {
    display: flex;
    flex-direction: column; /* Stacks items vertically by default (Mobile) */
    gap: 20px; /* Adds space between the rows/columns */
  }

  /* When screen is 768px or wider, switch to columns */
  @media (min-width: 768px) {
    .responsive-container {
      flex-direction: row;
      align-items: flex-start; /* Aligns items to the top */
    }
    
    .responsive-item {
      flex: 1; /* Both items take equal width */
      width: 45%; /* specific preference from your snippet */
    }
    
    /* Replaces the inline margin-right */
    .responsive-item:first-child {
      margin-right: 5%; 
    }
  }
</style>

<div class="responsive-container">
  <div class="responsive-item">
  
```latex
\documentclass{article} % Starts an article

\begin{document} % Begins a document
Hello World!
\end{document}
```
  
  </div>
  <div class="responsive-item">
    <p>which renders to</p>
    <div style="height: 300px; border: 1px solid #ddd;"> <embed src="/_includes/assets/2026-02-01/hello_world.pdf" width="100%" height="100%" type="application/pdf">
    </div>
  </div>
</div>

## Building the CV template

LaTeX offers many different document types we can use, including the [`moderncv`](https://github.com/xdanaux/moderncv) document class.

The following snippet is incomplete and won't build
```latex
\documentclass{moderncv}

\begin{document}
Hello World!
\end{document}
```

We need to define at least the name of the CV holder, which is very straight forward.
You can look up the options in the [manual](https://github.com/xdanaux/moderncv/blob/master/manual/moderncv_userguide.v2.pdf).

```latex
\documentclass{moderncv}

\name{Philipp}{Zettl}
\begin{document}
Hello World!
\end{document}
```

and before we dive deeper, we will set the following three attributes on the document
- page size: DIN-A4
- font size: 11pt
- font type: Sans

Apart from that we chose one of the available designs of moderncv, e.g. `casual`, set the geometry of a page using the `geometry` package and enabling UTF-8 character sets for our input documents

<div class="responsive-container">
  <div class="responsive-item">
  
```latex
\documentclass[11pt,a4paper,sans]{moderncv} 

\moderncvtheme[green]{casual}

\usepackage[utf8]{inputenc}
\usepackage[scale=0.8]{geometry}
\recomputelengths

\name{Philipp}{Zettl}

\begin{document}
Hello World
\end{document}
```
  
  </div>
  <div class="responsive-item">
    <p>This still renders the same document</p>
    <div style="height: 300px; border: 1px solid #ddd;"> <embed src="/_includes/assets/2026-02-01/hello_world2.pdf" width="100%" height="100%" type="application/pdf">
    </div>
  </div>
</div>

Great, now we can start writing our actual CV!

First, we'll set a title and build up the structure of the CV
1. Professional Summary
2. Skills
3. Professional Experience
4. Projects
5. Education
6. Other



<div class="responsive-container">
  <div class="responsive-item">
  
```latex
\documentclass[11pt,a4paper,sans]{moderncv} 

\moderncvtheme[green]{casual}

\usepackage[utf8]{inputenc}
\usepackage[scale=0.8]{geometry}
\recomputelengths

\name{Philipp}{Zettl}

\begin{document}
\makecvtitle % renders name in CV head

\section{Professional Summary}

\section{Skills}

\section{Experience}

\section{Selected Projects}

\section{Education}

\section{Other}

\end{document}
```

  </div>
  <div class="responsive-item">
    <div style="height: 500px; border: 1px solid #ddd;"> <embed src="/_includes/assets/2026-02-01/hello_world3.pdf" width="100%" height="100%" type="application/pdf">
    </div>
  </div>
</div>

and if we fill out our personal data a little more, we even get the job title as a sub-header.

<embed src="/_includes/assets/2026-02-01/hello_world4.pdf" width="100%" height="50%" type="application/pdf">

## Filling the structure
To fully utilize the capabilities of LaTeX and because we love software we now fill our structure with dynamic content!

We'll do that using `Jinja2` and a `YAML` file.

```python
import yaml
import jinja2
import os
import subprocess

# Configuration
DATA_FILE = 'cv_content.yaml'
TEMPLATE_FILE = 'cv_template.tex'
OUTPUT_TEX = 'cv_rendered.tex'

def build_pdf():
    # 1. Load the YAML data
    with open(DATA_FILE, 'r') as f:
        data = yaml.safe_load(f)

    # 2. Setup Jinja2 environment with LaTeX-friendly delimiters
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('.'),
        block_start_string='\\BLOCK{',
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        comment_start_string='\\#{',
        comment_end_string='}',
        trim_blocks=True,
        lstrip_blocks=True
    )

    # 3. Render the template
    template = env.get_template(TEMPLATE_FILE)
    rendered_tex = template.render(**data)

    # 4. Write the output .tex file
    with open(OUTPUT_TEX, 'w') as f:
        f.write(rendered_tex)
    
    print(f"Generated {OUTPUT_TEX} successfully.")

if __name__ == "__main__":
    build_pdf()
```
As you can see we will use `\VAR` to access variable content and `\BLOCK` to initialize Jinja block entities.

Now, we "just" need to rewrite our template for the Jinja syntax

```latex
\documentclass[11pt,a4paper,sans]{moderncv}

% ModernCV themes
\moderncvstyle{\VAR{config.style}}
\moderncvcolor{\VAR{config.color | default('blue')}}

% Character encoding
\usepackage[utf8]{inputenc}

% Adjust the page margins
\usepackage[scale=0.75]{geometry}

% Personal data
\name{\VAR{config.name_first}}{\VAR{config.name_last}}
\title{Backend Engineer}

\begin{document}
\makecvtitle

\section{Professional Summary}
\cvitem{}{\VAR{summary | default('Passionate researcher with a focus on automation.')}}
\end{document}
```


Using the configuration

```yaml
config:
  name_first: "Philipp"
  name_last: "Zettl"
  theme_color: "blue"
  style: "casual"

summary: |
  Backend Engineer with 8+ years of experience building scalable Python systems and
  leading technical teams. Specialized in Django-based microservices, ML integration,
  and platform architecture. Architected AI automation platform that processed 2M+
  messages and spun off into easybits GmbH. Strong track record progressing from
  working student to founding engineer, mentoring teams of 3-5 developers, and
  driving engineering practices from prototype to production.

```
and the command

```shell
uv run python ./build.py
```
This gives us the beautiful render of

<div style="height: 500px; border: 1px solid #ddd;"> <embed src="/_includes/assets/2026-02-01/hello_world5.pdf" width="100%" height="100%" type="application/pdf">

With this we can now push more content into our template.

In case you're interested in my final solution head over to my [github profile-repository](https://github.com/philsupertramp/philsupertramp).
It includes the python script, yaml config and the template file as well as a github action CI/CD that builds the whole CV.

That being said, good luck with your CV and in case you have questions feel free to reach out to me :-)
