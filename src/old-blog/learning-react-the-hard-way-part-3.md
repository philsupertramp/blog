---
title: "Learning React(JS) the hard way Part 3"
cover: "/images/eli-francis-100644-unsplash.jpg"
author: "phil"
date: 2019-05-26
tags:
    - full-stack
    - development                                   
    - stuff
    - other
    - published
    - old-blog
layout: mylayout.njk
---


## My private package hell (The intro)


Oh boy, oh boy. I hope you're as excited as I am!

<div><img src="https://media.giphy.com/media/3o7qDWZchVN4R4X5zG/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>


**Here a small recap of what we know:**

React is currently one hell of a popular library for the programming language JavaScript. In the time between May
2018 and now the monthly amount of downloads increased about 300%. 

![Downloadstats from npmjs.org for the package <a href="https://npm-stat.com/charts.html?package=react">React</a>]({{ '/_includes/assets/old_blog/npm_stats_react_yearly.png' | url }})


React calls itself _"A JavaScript library for building user interfaces"_. And at least in my opinion it does a good job 
doing that! During the last weeks I was trying to find reasons not to like JavaScript and React. But every time I open my 
IDE and code for some time, I experience new and awesome stuff which helps me to improve me and my products. Since you're hopefully here since my
[first post](/old-blog/learning-react-the-hard-way-part-1) in this "series", you may caught up some sarcastic or ironic vibe.
Sorry about that, pal. I'll try to keep it to a minimum **amount**.

<div><img src="https://media.giphy.com/media/TKWteu8wW5PTayafmj/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

What keeps me thinking negative about JS is the **amount** of public available, unmaintained, outdated, unorganized and not well documented packages on their 
package index.  
At the end of my first post I mentioned one of the first problems I've faced within my early hours of learning JS.

#### This is what I wanted to write, before I fake checked myself...
<details style="margin-bottom: 5rem;"><summary>Click me</summary>
<p>
There's no such thing as a well implemented built-in date API. Just get used to it. 

And here's the deal:
> most of my applications depend on calculations of time

So I started to develop a routine for me to test a new language or framework to fit my chore requirements.  
Here we are. No built-in date API to calculate with.
</p>
</details>

#### This is actually true...

During research for this article I found out I'm able to use the built-in `Date`-API of JS for all the stuff I need, so I
can finally get rid of one of the biggest packages in my current dependency tree!
<div><img src="https://media.giphy.com/media/LFqxF9yF8sRry/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

> What's the problem, I don't get it?

The idea of my first JS script was to determine date and time in a selected timezone for a specified datetime in the same or another timezone.

Basically  
Input:  
  - DateTime /+ Timezone
  - Timezone  

Output:
  - DateTime

My pythonic way is pretty simple. There's the simple solution, for which the user is responsible of checking the input parameters. 
And the advanced OOP version, which would end in a lot of fun, I swear! Plus for now we don't need localized formats at all! =D
<details style="margin-bottom: 5rem;"><summary>short Python example</summary>
<p>

BTW did you ever realize that imports in JS are `import method from 'package'` and in Python it's the opposite order? funky. Confuses me every time!
```python
import pytz
from datetime import datetime

def localize_datetime(dt: datetime, tz: str) -> datetime:
    timezone = pytz.timezone(tz)
    return timezone.localize(dt)
```
**Disclaimer**: This approach will obviously fail for situations in which the user provides wrong input parameters.
</p>
</details>
But what to do if you're not familiar with a language and you want to do best practice since day one? You start googleing
you problems. 

This became in most situations one of my easiest tasks, research. But for many people it's still a problem. In the beginning of ones development career, a modern developer, 
is this huge problem of asking the right question. I would love to give some knowledge on how to improve your search queries and how to find good 
quality content. Sadly I'm not quite sure how to do so, but there're plenty of nice post about peoples experiences and their learning curve on [reddit](https://www.reddit.com/r/learnprogramming/comments/2fmaxp/how_long_was_your_learning_curve/).
You should seriously check out that link, there are awesome stories!

#### The entrance

Doing research for my script turned out to be a perfect example and my entrance into the package hell. Everyone online recommends to 
>just search for a package at npmjs.org
<div><img src="https://media.giphy.com/media/12pMNuLbibieaY/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

As mentioned in my [first post](/old-blog/learning-react-the-hard-way-part-1), a search for the packages related to the keyword "time"
on 12th of May 2019, 24 day before today (26th May 2019), hit 13470 results. Today, we're at 13597.

![Search results for "time"]({{ '/_includes/assets/old_blog/post-4-time.png' | url }})

Adding 127 packages within three and a half weeks feels a lot of possible bullshit, right? 
Maybe my bullshit detector is broken and I just should give it a try. So I ended up installing and trying several packages.
Sounds fine so far – at least for me – but what I didn't expect was to keep record of all the packages I installed 
and never used after I realized that they are not what I was looking for. 
At the end I installed about 10 packages, and `moment.js` was one of them.

I thought I found a nice companion for the end of my days. `moment`s usage is awesome, I really like it! No unnecessary crap and imports. 
Clean usage of a nice package [(check it out if you can)](https://momentjs.com/)!  
Except the fact that it's one of the biggest packages I ever worked with. The first build of my first project was about 8.9MB big.
And I seriously tried to deploy that crap. I didn't knew better. Didn't check my dependencies or if I have unused packages and garbage in my code.  
As we germans say, I was green behind my ears.

But that was just the beginning.

<div><img src="https://media.giphy.com/media/3o6ZtrdYJF3BbgATAI/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>


#### Sorry, buddy

Again the time is over.. As every week I thank you for reading my post, I hope you enjoyed it!  
_Catch you on a flip flop_. See you in [part 4](/old-blog/learning-react-the-hard-way-part-4)! 
<div><img src="https://media.giphy.com/media/hs8SqOYWARxO8/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>
Enjoy your weekend

Phil
## Credits

Title image:
<a style="background-color:black;color:white;text-decoration:none;padding:4px 6px;font-family:-apple-system, BlinkMacSystemFont, &quot;San Francisco&quot;, &quot;Helvetica Neue&quot;, Helvetica, Ubuntu, Roboto, Noto, &quot;Segoe UI&quot;, Arial, sans-serif;font-size:12px;font-weight:bold;line-height:1.2;display:inline-block;border-radius:3px" href="https://unsplash.com/@elifrancis?utm_medium=referral&amp;utm_campaign=photographer-credit&amp;utm_content=creditBadge" target="_blank" rel="noopener noreferrer" title="Download free do whatever you want high-resolution photos from Eli Francis"><span style="display:inline-block;padding:2px 3px"><svg xmlns="http://www.w3.org/2000/svg" style="height:12px;width:auto;position:relative;vertical-align:middle;top:-2px;fill:white" viewBox="0 0 32 32"><title>unsplash-logo</title><path d="M10 9V0h12v9H10zm12 5h10v18H0V14h10v9h12v-9z"></path></svg></span><span style="display:inline-block;padding:2px 3px">Eli Francis</span></a>


## Sources
- [npmjs download stats React](https://npm-stat.com/charts.html?package=react)
