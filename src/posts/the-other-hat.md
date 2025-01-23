In the end of last year the company I'm working for was going through a transitional period in which we needed to recreate our infrastructure on a second set of accounts for each product.

Of course, instead of creating two new environments to host the two applications, we cut down one and created a second.

We were quite convinced by the fact that it's a more or less blunt task and not more than manually setting up some security relevant things and running a bunch of commands.

Heck, after all we so proudly use `terraform` for our infra, even our apps are deployed using `helm`.
To put the cherry on top of this Infrastructure as Code [IaC] sundae we use `terragrunt` to keep things organised and structured.

Let's briefly bring up exhibit A 