---
title: "Learning React(JS) the hard way Part 4"
cover: "/images/jenny-marvin-698502-unsplash.jpg"
author: "phil"
date: 2019-06-01
category: "tech"
tags:
    - stuff
    - other
    - published
    - old-blog
layout: mylayout.njk
---


Hey there pal,  
another week another episode of by story on how I learned React(JS) the hard way. Since I never said that before and
really want to clarify some things, a short passage before the real article begins.
>>> The following post contains code, which is tested by myself. If you intend to use this piece of software
feel free to do so. Please be aware that this is by far not production ready and should be reviewed by a person with an
advanced knowledge of JavaScript. I don't claim to have this knowledge, neither do I want to transfer you knowledge on how
to write a specific program nor is this a "How to JavaScript 101". I intend to tell you a personal and hopefully interesting
story of my life. And I want to prevent people doing the same mistakes I did.

One of my biggest problems from the beginning was to decide between packages. I started reading a
huge pile of blog posts about which package should be used in what some kind of case, but mostly it is opinion based. What I did not know was the fact that there
could be packages which are better to use on frontend and packages you should definitely not use in your
frontend application. Sucks, huh? I was searching for an extended Date API. As mentioned in my previous [blog
post](/old-blog/learning-react-the-hard-way-part-3/) each of my applications depends on calculating a bunch of dates in different
units. For example adding 2 years to a date, or to determine if a user is above 18 or not. Basically
all that stuff we learned in elementary school. But not for computers since they know how to use logical and
mathematical operators by themselves they decided to drop out of school.
<div><img src="https://media.giphy.com/media/l2JdW2IDm9XCwpfRS/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

Since I was under a bit of time pressure and needed to get things done fast, I decided to check out several libraries.
_Keep in mind that I started this app literally from zero. No knowledge about how this new JS works and how to use it
properly._ And got stuck at some fancy ass library called [moment-js](https://moment.org). Spoiler alert, this is a huge
library and it is able to do way more stuff than I needed. My thoughts about that tended to be super positive. I mean c'mon
it's better to have what you don't need than needing something and don't have, right?

### The downside
React is designed to serve a client rendered single page application.  
... Can't you see it coming?
<div><img src="https://media.giphy.com/media/GpFxyI3AIk8es/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

Turns out that sending big packages to your client is not so nice as you think!

I guess some people are thinking right now
> Why do you stick with a library that does not fulfill your requirements?

Imagine the following scenario:  
Since you are super interested in airplanes you decide to travel on your next vacation by plane,
it turns out that you're the only person taking that particular flight, but the
airline is using an AirBus A380, "Just for you".

Side facts:  
If you deny using this aircraft because of the fact that this aircraft is way too big just for one person,
you would need to try to take the next airplane with a 99.9% chance of **not** getting a seat, because this flight is already overbooked.
Basically you would miss your holiday.

Now ask yourself these questions:
Would you deny your flight?
Or would you maybe start tearing apart a plane during flight just because you want to know how it works?

I know this scenario isn't as real as mine, I just wanted to put you in the same position in which I was not that long ago.

>>For those of you who read since [post No. 1](/old-blog/learing-react-js-the-hard-way-part-1):
>>>I know I mentioned in the previous posts that I am working with next-js, so the date calculation could
take part during the cycle of rendering on server side. The following is just an example, which I still feel more
comfortable about than using a huge 3rd party package. I can test and adjust the functionality as I want. This
philosophy is manifested in my mind since I needed to write every single functionality of the software I created during
assignments and tasks in university.

One day I came up with a plan, which is straight forward and was the first thing that came to my mind.
>I gotta need to replace that flagship!

<div><img src="https://media.giphy.com/media/g0mzdiXspEFYdH0ojf/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

But you can't kill what you don't know. And knowing everything about your enemy isn't bad at all. I mean how else would
you stalk someone if you don't know where he is, right? ┬┴┬┴┤(･_├┬┴┬┴

# The plan
Let's break it down real quick. All we need to do is

1) determine used functionality
2) create requirements
3) start creating the small package
4) replace only imports
5) fix bugs
6) be happy


So all we need to do is replace the currently used package with a self written version just containing the required
set of features. AWESOME!

> I still haven't written any piece of code with raw JS OOP

First things first!
- [x] determine used functionality
- [x] create requirements

```javascript
/*
* Constructors:
* - new Moment()
* - new Moment(secondDate, one of ['DD.MM.YYYY', 'YYYY-MM-DD', 'DD.MM.YYYY HH:mm'])
*
* Methods:
*   // diff between two Moment's
* - .diff(secondDate, one of ['m', 'd', 'y', 'minute', 'second', 'millisecond']])
*   // return in formatted string
* - .format(one of ['YYYY-MM-DD', 'DD.MM.YYYY'])
*   // add time unit to obj
* - .add(number, one of ['m', 'd', 'y', 'minute', 'second', 'millisecond']])
*   // determines if obj is valid
* - .isValid()
*   // getter for date units
* - .get(one of ['m', 'd', 'y', 'minute', 'second', 'millisecond'])
*   // explicit getter for Moment's weekday (and for real, we need to do it right!)
* - .weekday()
*/
```
- [x] determine used functionality
- [x] create requirements

I started object oriented programming by being forced to use C++.
>>>Today is **the** day! I am finally able to announce that I miss C++.

<div><img src="https://media.giphy.com/media/3o72EUYPgo7D0EXBiE/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

> You said you don't want to bash JS anymore!

True. Immutability of objects can be gained by 3rd party packages, and there are even some packages which
give you the ability to override operators. Like [immutable](https://www.npmjs.com/package/immutable) and
[operators](https://www.npmjs.com/package/operators). There're even some articles on [DYI operator overriding](http://2ality.com/2011/12/fake-operator-overloading.html)
which are damn good and super helpful. But on the other hand, again you depend on 3rd party software and the knowledge of
people writing articles. Do we really trust them enough to ship production ready code? Do we want our customers
to may be scammed or having a really bad experience, because the code wasn't cross platform compatible?
I may sound like a total moron and I should give more trust in the OS community. But the fact that I keep bumping into
outdated packages is soooo fucking annoying. For real.

Anyway, today I'm gonna start with my class `Moment`

<div><img src="https://media.giphy.com/media/t3DDmrHb2jSQE/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

Let's see, I know from React that there's a keyword `class`, but I also know – from reading [some](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes#Class_declarations)
[articles](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes#Boxing_with_prototype_and_static_methods)
– that one can use `function` for classes as well. Still don't know the difference yet, so I would prefer the `class` version
of a **class**.
```javascript
class Moment { };
```
There we go. React also introduced me to a constructor of an inherited model, which is obviously called `operator`.
If you inherit from another class you should add some parameter to get passed to `constructor` and "super"-call them, to
execute the parent constructor.

<div><img src="https://media.giphy.com/media/BdAn5S0xigpO/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

Since we don't inherit and want to have a base class for our purpose we can ignore that.
```javascript
class Moment {
    constructor() { };
}
```
Okay, now we have three requirements:
- [ ] constructor needs to accept the required parameters.
- [ ] we need either a set of constructors or a compatible constructor for multiple combinations of parameters.
- [ ] the constructor should **use** the parameter provided in a nice way, so operations will be fast as required.

First task? easy.
```javascript
class Moment {
    constructor (date, format) { };
}
```

- [x] operator needs to accept the required parameters.

<div><img src="https://media.giphy.com/media/uMSm9Q0XQLkSQ/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>

You wish!
Second task. The docs weren't saying anything about that, which feels super fucked up... **BUT** google revealed
the [holy grail](https://stackoverflow.com/a/3220903) which is basically saying one should tell the constructor
all possible parameters, than handle each combination as needed. **MANUALLY**.
At least we stay within our DRY ideology, right?
~~I was even reading about a way to [get rid of keyword `new`](https://css-tricks.com/understanding-javascript-constructors/#article-header-id-6).~~ ²  
Awesome, let's do it!

<a name="2019-06-09"></a>

<details style="background-color: #ccc; width: 100%; padding: 0.5rem"><summary>Before revision</summary>
<p>

##### Update 2019-06-09

Unfortunately the "hack" to replace the keyword `new` is not working as expected, hence I removed it. 
```javascript
class Moment {
    // passing the needed parameters
    constructor (date, format) {
        // using this fancy hack to replace `new`
        if (!(this instanceof Moment)) return new Moment(date, format)¹;
        // handling each type by itself…
        if(typeof date === 'undefined' && typeof format === 'undefined') 
            // parse date
        else if (typeof date === 'string' && typeof format === 'string') 
            // parse date
        else if (typeof date === 'object' || typeof date === 'number') 
            // parse date
        else throw 'Construction Error';
    };
}
```
</p>
</details>

```javascript
class Moment {
    // passing the needed parameters
    constructor (date, format) {
        // handling each type by itself…
        if(typeof date === 'undefined' && typeof format === 'undefined') 
            // parse date
        else if (typeof date === 'string' && typeof format === 'string') 
            // parse date
        else if (typeof date === 'object' || typeof date === 'number') 
            // parse date
        else throw 'Construction Error';
    };
}
```
- [x] we need either a set of constructors or a compatible constructor for multiple combinations of parameters.

Wow, I even added a meme...
> Me: passing wrong params to Moment  
Moment: CONSTRUCTION ERROR!!!!!!1!11!<div><img src="https://media.giphy.com/media/bLxrToqfjThYs/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>



Not that bad for a first approach, one step left until we can use this rocket.
Parsing the data is probably the most important thing for a construction, just joking.
But for real, how to parse it in a nice way to avoid duplication and to use the data as needed?

```javascript
class Moment {
    // passing the needed parameters
    constructor (date, format) {
        // handling each type by itself…
        // create as today
        if(typeof date === 'undefined' && typeof format === 'undefined')
            this.date = new Date();
        // parse date through string
        else if (typeof date === 'string' && typeof format === 'string')
            this.date = new Date(date);
        // parse date through Date object 
        // or number (milliseconds from `new Date().valueOf()`)
        else if (typeof date === 'object' || typeof date === 'number')
            this.date = new Date(date);
        else throw 'Construction Error';
    };
}
```
- [x] the constructor should **use** the parameter provided.

But wait, that's shit!
<div><img src="https://media.giphy.com/media/dfNYKfFIbI1a0/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>


> We don't use format at all, why do we even need it?
>> It was part of the requirement, `moment`-js parses strings with a format string. I want to keep that to
minimize the refactoring costs (even though it's almost nothing).

> We can simplify the 2nd and 3rd statement to share one case
>> Cheers, mate! That's some fine idea. I would also remove the test for format, since we don't care about it at all.
Another improvement I had in mind was to keep the raw value of a `Date` object, since we are so smart and calculate with
milliseconds like there's no tomorrow. Keeping the data type simple to gain performance and built-in features feels
like a good decision.

Improvement
```javascript
class Moment {
    // passing the needed parameters
    constructor (date, format) {
        // handling each type by itself…
        if(typeof date === 'undefined' && typeof format === 'undefined')
            this.date = new Date();
        else if (typeof date === 'string'
            || typeof date === 'object'
            || typeof date === 'number')
            this.date = new Date(date);
        else throw 'Construction Error';
        // parse the value for faster operations
        if(this.date) this.value = this.date.valueOf();
    };
}
```
<div><img src="https://media.giphy.com/media/l2YWlvtHGTbawriU0/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>



## Don't you hate me?
This series of blog posts turns out to be waaaaay bigger than expected, but I am happy every day to see this blog evolving 
and I am really excited for each visitor on my page.

For all of you who are into security and the fact that even in the "free web" you are watched by everyone, I totally get
the point of protecting your own privacy. This page uses – as you can see within it's code – Google Analytics. 
~~(For more information check out the [privacy page]()).~~
Which will be 
one of the topic of one of my future posts. But maybe in a way you don't know it yet. 	(̿▀̿ ̿Ĺ̯̿̿▀̿ ̿)̄

Next week I will continue creating the small date library to get finally rid of 50% of the size of my app! Incredible un-zipped 200kB.

Enjoy your weekend 

> Catch you on the flip flop!
<div><img src="https://media.giphy.com/media/TMYtIzAY30BGg/giphy.gif" style="width: 90%; margin-left: 5%;margin-bottom: 5rem"/></div>



¹: [Updated 2019-06-09](#2019-06-09)

## Credits
- Title image: <a style="background-color:black;color:white;text-decoration:none;padding:4px 6px;font-family:-apple-system, BlinkMacSystemFont, &quot;San Francisco&quot;, &quot;Helvetica Neue&quot;, Helvetica, Ubuntu, Roboto, Noto, &quot;Segoe UI&quot;, Arial, sans-serif;font-size:12px;font-weight:bold;line-height:1.2;display:inline-block;border-radius:3px" href="https://unsplash.com/@jennymarvin?utm_medium=referral&amp;utm_campaign=photographer-credit&amp;utm_content=creditBadge" target="_blank" rel="noopener noreferrer" title="Download free do whatever you want high-resolution photos from Jenny Marvin"><span style="display:inline-block;padding:2px 3px"><svg xmlns="http://www.w3.org/2000/svg" style="height:12px;width:auto;position:relative;vertical-align:middle;top:-2px;fill:white" viewBox="0 0 32 32"><title>unsplash-logo</title><path d="M10 9V0h12v9H10zm12 5h10v18H0V14h10v9h12v-9z"></path></svg></span><span style="display:inline-block;padding:2px 3px">Jenny Marvin</span></a>

<script>
$('.gifplayer');
$('.gifplayer').gifplayer();

$gifs = $('.gif');

$gifs.each(function (i, gif) {
    $(gif).data('isPlaying', false);
});


$(window).scroll(function () {
    $gifs = $('.gif');

    $gifs.each(function (i, gif) {
        $gif = $(gif);

        if ($gif.visible(true)) {
            if (!$gif.data('isPlaying')) {
                $gif.find('.gifplayer').gifplayer('play');
                $gif.data('isPlaying', true);
            }

            if ($gif.find('.gp-gif-element').length > 1) {
                $gif.find('.gp-gif-element').first().remove();
            }
        } else {
            if ($gif.data('isPlaying')) {
                $gif.find('.gifplayer').gifplayer('stop');
                $gif.data('isPlaying', false);
                console.log('Play')
            }
        }
    });
});
</script>

