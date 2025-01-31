---
title: "Learning React(JS) the hard way Part 2"
cover: "/images/gareth-harrison-1390194-unsplash.jpg"
author: "phil"
date: 2019-05-19
tags:
    - full-stack
    - development
    - published
    - old-blog
layout: mylayout.njk
---

_Hey friend, this is the second part of my small series about me getting introduced to JS._

 - _If you're here by accident and actually wanted to read the whole story [click here](/old-blog/learning-react-the-hard-way-part-1)._  
 - _If you're just interested in my first impression of React and you don't actually care about the background, keep on reading._
 - <a style="text-decoration: none; cursor: text" target="_blank" href="/images/r2-d2-c-3po-best-friends-wallpaper-5478.jpg"><i>These</i></a> _are definitely not the druids you are looking for._


## We are definitely not close
In late 2018 I started working as a python backend developer for a ML driven platform which basically matches future 
employers, so called job candidates with jobs within hours (sometimes a few days).
<div><img src="https://media.giphy.com/media/d2YZzTQvyoNYf9YI/giphy.gif" style="width: 90%; margin-left: 5%"/></div>


enough ads!


During december 2018 my boss introduced me to the idea of being a full stack developer. As far as I remember I said during
my interview for exact this job position 
>Please don't ask me to do frontend tasks, I hate the accuracy you need to vertical align two divs

Now I hear people saying "Just use the damn `flex-box`, idiot". But let's keep to the fact that you have thousands of 
different attributes which can define the exact same state. And it's just too hard for me to decide whether to use low-level 
attributes like `left` instead of a `margin-left`, or chose `order` because the fancy `flex` gives me purrrrfect alignment.

<div><img src="https://media.giphy.com/media/O7FZoSMAgF9f2/giphy.gif" style="width: 90%; margin-left: 5%"/></div>

Anyway I didn't refuse the offer and started learning JavaScript – as mentioned in [my last post](/old-blog/learning-react-the-hard-way-part-1).



### Which turns out to be the greatest idea of my whole life?
_Don't think so._

Yes, I use JS in multiple projects, since I learned it. But isn't that just common sense? Why to forget something because
you don't like it? Is it the fear of incompatibility with your current tech stack?  

For me it was just inconvenient to learn those "silly" languages, as 
[C++](https://en.wikipedia.org/wiki/C%2B%2B), 
[C](https://en.wikipedia.org/wiki/C_(programming_language)), 
[R](https://en.wikipedia.org/wiki/R_(programming_language)), 
[MATLAB](https://en.wikipedia.org/wiki/MATLAB) 
and [SAS](https://en.wikipedia.org/wiki/SAS_(software)). 
In my perspective I feel like I've traveled a lot through languages and was happily surprised when I dug into Python by 
writing small helpful scripts. To be hones... it's easy. A few rules to follow and the sky is the limit 🚀.

But today I'm here to tell you something about my experience with JavaScript and especially my dear friend [ReactJS](https://reactjs.org).

<div><img src="https://media.giphy.com/media/25KEhzwCBBFPb79puo/giphy.gif" style="width: 90%; margin-left: 5%"/></div>

After reading through several topics of "[The Modern JavaScript Tutorial](https://javascript.info/)", scripting a few things 
aaaaaaaaand the beautiful support through the fantastic [Tutorial: Intro to React](https://reactjs.org/tutorial) I felt 
wise enough to start writing my first small page using react and [nextJS](https://nextjs.org/) for SSR support. I also needed to set up an
express server to achieve SSR support. The schema is a bit different to regular React because of nextjs, but I guess 
you'll get the gist, since I got it. ;)

So I ended up with a directory like that

![React|NextJS dir]({{ '/_includes/assets/old_blog/react-1-dir.jpg' | url }})


with my `index.js`:
```javascript
import React from 'react'
export class App extends React.Component {
  render() {
    return (
      <div>
        <h1>Hello World!</h1>
      </div>
    )
  }
}
export default App
```
and `server.js`
```javascript
const express = require('express')
const next = require('next')

const port = parseInt(process.env.PORT, 10) || 3000
const dev = process.env.NODE_ENV !== 'production'
const app = next({ dev })
const handle = app.getRequestHandler()
app.prepare().then(() => {
  const server = express()
  server.get('*', (req, res) => {
    return handle(req, res)
  })

  server.listen(port, err => {
    if (err) throw err
    console.log(`> Ready on http://localhost:${port}`)
  })
})
```

So I started with my first version of a "Component", because **components are React** or is React components? (/•-•)/:
#### 1st version:
```javascript
import React from 'react'
export class MyComponent extends React.Component {
  render() {
    return (
      <div>
        <h1>Hello World!</h1>  
      </div>
    )
  }
}
export default MyComponent
```

#### 2nd version:
```javascript
import React from 'react'
export const MyComponent = () => {
  return (
    <div>
      <h1>Hello World!</h1>  
    </div>
  )
}
export default MyComponent
```

#### 3rd version:
```javascript
import React from 'react'
export const MyComponent = () => (
  <div>
    <h1>Hello World!</h1>  
  </div>
)

export default MyComponent
```
As you can see the evolution of this component is from a 
"[React Class Component](https://www.robinwieruch.de/react-component-types/#react-class-components)" 
to a "[React Functional Component](https://www.robinwieruch.de/react-component-types/#react-function-components)". 
Maybe you get my point already, but let's say we add for example some functionality to our component. Let's pass a variable
"`title`" through to display within our `h1`-tag.

>_For convenience I continue with version 1 and 2, because 3 is obviously just a shorter version of 2_

#### 1st version:
```javascript
import React from 'react'
export class MyComponent extends React.Component {
  render() {
    return (
      <div>
        <h1>{this.props.title}</h1>  
      </div>
    )
  }
}
export default MyComponent
```

#### 2nd version:
```javascript
import React from 'react'
export const MyComponent = ({title}) => {
  return (
    <div>
      <h1>{title}</h1>  
    </div>
  )
}
export default MyComponent
```

The usage of our components is equal, we can use both within `pages/index.js`:
```javascript
 import React from 'react'
+import MyComponent from '../src/components/MyComponent'
 export class App extends React.Component {
   render() {
     return (
-     <div>
+       <MyComponent title={'Hello World!'}/>
-     </div>      
     )
   }
 }
export default App
```

![Screenshot of http://127.0.0.1:3000]({{ '/_includes/assets/old_blog/website-1.png' | url }})


<div><img src="https://media.giphy.com/media/l0IypeKl9NJhPFMrK/giphy.gif" style="width: 90%; margin-left: 5%"/></div>

### Incredible website, I know!
But as you can imagine, this is just one way to do it. There're several other ways to reach one goal. And different options
can end in different scenarios. So be careful by choosing the wrong component type! 

>Here's a tip from my side, which might be wrong, but it works pretty good for me. I always start with class components

JavaScript and 
especially ReactJS as a framework update their standards so frequently, that I don't feel super confident 
about big JavaScript projects. But why not trying to keep your code base up to date! In my opinion it's not a goal to
refactor your whole project once per year, just because there's a new fancy way of doing it. 
Why should we change a running system?

In that moment most of the people think about the possible options how to use this and how awesome it will be in the future.
All I can think about is:
> Dude! That wasn't even 10 minutes and you can basically increase your productivity by quitting to use basic HTML and use
React even though you're building a static page. 

Reusable Com... Com... 

## Reusable Components
Sorry again friend, I need to postpone the topic about packages and libraries for Post #3 
[Learning React(JS) the hard way Part 3](/old-blog/learning-react-the-hard-way-part-3). If you like reading so far and want to
give me nice feedback hit me per <a href="mailto:phil@godesteem.de">Mail</a> or try to contact me in other known ways.

<div><img src="https://media.giphy.com/media/l4FAYTEssy5ux9zlm/giphy.gif" style="width: 90%; margin-left: 5%"/></div>


Enjoy your weekend

Phil

#### Credits:

Title Image: 
<a style="background-color:black;color:white;text-decoration:none;padding:4px 6px;font-family:-apple-system, BlinkMacSystemFont, &quot;San Francisco&quot;, &quot;Helvetica Neue&quot;, Helvetica, Ubuntu, Roboto, Noto, &quot;Segoe UI&quot;, Arial, sans-serif;font-size:12px;font-weight:bold;line-height:1.2;display:inline-block;border-radius:3px" href="https://unsplash.com/@gareth_harrison?utm_medium=referral&amp;utm_campaign=photographer-credit&amp;utm_content=creditBadge" target="_blank" rel="noopener noreferrer" title="Download free do whatever you want high-resolution photos from Gareth Harrison"><span style="display:inline-block;padding:2px 3px"><svg xmlns="http://www.w3.org/2000/svg" style="height:12px;width:auto;position:relative;vertical-align:middle;top:-2px;fill:white" viewBox="0 0 32 32"><title>unsplash-logo</title><path d="M10 9V0h12v9H10zm12 5h10v18H0V14h10v9h12v-9z"></path></svg></span><span style="display:inline-block;padding:2px 3px">Gareth Harrison</span></a>
