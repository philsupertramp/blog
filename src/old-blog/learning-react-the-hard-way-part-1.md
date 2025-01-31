---
title: "Learning React(JS) the hard way Part 1"
cover: "/images/second_post.jpg"
author: "phil"
date: 2019-05-12
category: "tech"
discussionId: "2019-05-12-learning-react-js-the-hard-way-part-1"
tags:
    - development
    - stuff
    - other
    - published
    - old-blog
layout: mylayout.njk
---

Or 
# How my code quality started to decrease

When I got introduced to [ReactJS](https://reactjs.org) JavaScript was nothing bigger for me than *jQuery* and changing
some DOM elements using event handlers.

To be honest from that point of view there was no explanation how those 
weird HTML files with a super suspicious content like
```html
<!DOCTYPE html>
<html lang="en">
<head>
<title>Some page title</title>
</head>
<body>
<script src="/bundleA.js"></script>
<script src="/bundleB.js"></script>
<script src="/bundleC.js"></script>
<script src="/bundleD.js"></script>
<script src="/bundleE.js"></script>
</body>
</html>
```
inject all the content needed for a single page application.

<div><img src="https://media.giphy.com/media/8vLrx3xC3xpeYGXXVm/giphy.gif" style="width: 90%; margin-left: 5%"/></div>

Well anyway, I guess you get the gist. The current JS was not even close familiar to me. But I was curious so I started 
reading into JS and actually started to like it.

One of the tweaks I like in JS is the fact that you're able to write a small logical statement in a short 
version. For example JS' support for the `?`-operator

```javascript
for(let i = 1; i <= 100; i += 1)
  console.log(i, i % 5 ? "fizz" : "", i % 7 ? "buzz" : "");
```

But my favourite are the arrow functions
```javascript
window.onscroll = () => alert("NO!");
```
<div><img src="https://media.giphy.com/media/P0d4NSUbhl6ww/giphy.gif" style="width: 90%; margin-left: 5%"/></div><br/>

### But wait! 

There's a **dark** side. But `dark != bad`, right?  
Or is it `dark !== bad`. I'm not sure.  
Has dark the same type? If so, do I want to compare types?  
Still, I'm confused.  
Let's try it a different way.

Give both "variables" a *type*. 
For now we define  
`dark = 0` from type Number and  
`bad = "0"` from type String

both receive the value 0, as if we would put each variable on a scale in it's universe. So the value for dark would be 0 in
0 to 10, dark to bright and bad receives 0 for 0 to 10, bad to good. Logical, right?

```javascript
> let dark = 0;
> let bad = "0";
> bad != dark
false
> bad !== dark
true
```
What's that crappy `!=`? Instead we receive the new born child `!==`.  
The operator which I know since my dawn of programming... gone. 
<div><img src="https://media.giphy.com/media/Ahtg0hh0edZAs/giphy.gif" style="width: 90%; margin-left: 5%"/></div>

I continue studying this operator, keep digging to understand it.  
Digging deeper and deeper, day for day.  

>Captain's log: Half of my crew left my after I introduced the idea of digging deeper into this operator hell. I started to see curious combinations. Once I wanted to understand how the type comparison works for `Object`\'s.  I lost the other half of my crew after I tried

```javascript
> Object() == {}
false
> Object() === {}
false
> typeof(Object())
"object"
> typeof({})
"object"
```
<img alt="thinking meme" src="/images/thinking_meme.jpg" style="width: 20%; margin-right: 5%"/> HMMMMMMMMMMMMMMMMMMM 

```javascript
> typeof(Object()) == typeof({})
true
> typeof(Object()) === typeof({})
true
```
Never mind seems like I search for a reason to hate the language. 
But it could be worse, right?  
Ever heard of *libraries/packages*? Awesome shit! 

Imagine this:

>You're thinking about a feature you could add to your codebase, which calculates the correlation of a set of time intervals. The built in JS API `Date` does not give you the full set of features you need to get this job done. You do research for a package or library which supports your required set of features. Since you're familiar with the beloved package manager **npm** you know [npmjs.org](https://npmjs.org).  Let's hit the search. [...result](https://www.npmjs.com/search?q=time)

![npm search "time"]({{ '/_includes/assets/old_blog/npm_search_time.png' | url }})

1347 search results. Ha! Easy choice, right?  

In the next post ([Learning React(JS) the hard way Part 2](/old-blog/learning-react-js-the-hard-way-part-2)) 
I will introduce you to my personal package hell and how I started to learn the *real* ReactJS, not JS like today.
<div><img src="https://media.giphy.com/media/aq23msctvnd4Y/giphy.gif" style="width: 90%; margin-left: 5%"/></div><br/>

See you next week
Phil

