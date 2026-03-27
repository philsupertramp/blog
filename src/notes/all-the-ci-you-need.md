---
tags:
 - note
 - published
 - devops
 - automation
title: "All the CI/CD YOUR Project needs"
layout: mylayout.njk
author: Philipp
description: In this short post we'll explore if we actually need CI/CD for our private projects, or not.
date: 2026-02-18
---
Recently I started diving deeper into Rust and started building a tool that targets ARM devices.

In case you don't work with a Apple's M chip series or on an edge computer like the RaspberryPi, you most likely run an x86 architecture inside your machine. And so am I.

Rust comes with fancy decorators that prevent specific code to be compiled on non matching architectures. For example for my ARM project

```rust
#[cfg(target_arch = "aarch64")]
```

This allows me to compile the code on a different architecture and most importantly to be able to define different behavior for different architectures.

Great, so my tooling is already set in place for my project to work, even if I'm not on my target architecture.
But in most cases I also want to run or test my code on the target architecture, so I need a solution for this.

Introducing: **The Poor Mans CI/CD**

## The Poor Mans CI/CD
The poor mans CI/CD is basically just `git` and `ssh` running on your remote server.

In my network I have my machine `10.0.0.1` and my RaspberryPi `10.0.0.2`.

As prerequisite you need to install `git` and `ssh` and set up an `ssh` connection on the Pi. You can find a detailed guide on the [raspberrypi.com website](https://www.raspberrypi.com/documentation/computers/getting-started.html). I suggest the headless setup.

For simplicity we'll setup a tiny Python project that prints "Hello World", just because we don't need to setup a big environment on the RaspberryPi to get started.

### 1. create a directory on the local machine
```
> mkdir -p myproject
> cd myproject
```

Here's the script, let's call it `script.py`
```python
#!/usr/bin/env python
print("Hello World!")
```
Our current directory content is
```shell
> ls -la
-rw-r--r-- 1 phil phil 152 18. Feb 14:50 script.py
```

### 2. Setting up the remote repo
Great, now lets ssh into the RaspberryPi and set up everything there
```
> ssh pi@10.0.0.2
```

We need to first create a directory structure for our `remote` repositories, i.e. the place we push to.

```shell
> mkdir -p $HOME/remote/myproject.git
> cd $HOME/remove/myproject.git
```
Next we need to initialize a "bare" repo. We can push to "bare" repos
and they manage the state of our project. But they don't actually contain the plain code files
```shell
> git init --bare
hint: Using 'master' as the name for the initial branch. This default branch name
hint: is subject to change. To configure the initial branch name to use in all
hint: of your new repositories, which will suppress this warning, call:
hint:
hint: 	git config --global init.defaultBranch <name>
hint:
hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
hint: 'development'. The just-created branch can be renamed via this command:
hint:
hint: 	git branch -m <name>
Initialized empty Git repository in /home/pi/remote/myproject.git/
```

### 3. The CI/CD Hook "Magic"
For automation we'll use the `post-receive` hook of `git` (in case you want to know more about hooks check out [the docs](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)), which executes on the RaspberryPi immediately after a push is received inside the "bare" repository.

For this we need a destination directory on the Pi
```shell
> cd $HOME
> mkdir -p work/myproject
```
Then we need to create a hook script inside the bare repo
```shell
> cd $HOME/remote/myproject.git/hooks
> nano post-receive
```
Here we can add our CI/CD logic, for example the following
```bash
#!/bin/bash

# 1. Define variables
TARGET_DIR="/home/pi/work/myproject"
GIT_DIR="/home/pi/remote/myproject.git"
BRANCH="master"

while read oldrev newrev ref
do
    # Only deploy if the master/main branch is pushed
    if [[ $ref =~ .*/$BRANCH$ ]];
    then
        echo "--- deploy: Starting CI/CD for $BRANCH ---"

        # 2. Checkout the code to the target directory
        # --work-tree tells Git where to unpack the files
        # --git-dir tells Git where the history is
        git --work-tree=$TARGET_DIR --git-dir=$GIT_DIR checkout -f $BRANCH

        # 3. Enter the target directory
        cd $TARGET_DIR

        echo "--- deploy: Running Tests ---"
        python script.py

        echo "--- deploy: Complete! ---"
    else
        echo "--- deploy: Ref $ref received. Doing nothing: only the ${BRANCH} branch may be deployed on this server."
    fi
done
```

make it executable
```shell
> chmod +x post-receive
```

### 4. Connecting local and remote
Now that we set up the remote hooks and infrastrcuture we're ready to set our remote host and push the code!

On your local machine inside your `myproject` folder
```shell
> git init
> git remote add origin pi@10.0.0.2:remote/myproject.git
> git commit -m "init commit"
> git push origin master
```

And that's basically it!

## The extra mile
Now one might say
> This manual setup of the hook is tideous, can we change that?

And surely we can. We can store the hooks inside our repository, **but** need to tell our remote about it.

### 1. Moving hooks locally
To move the hooks into the repository, create on your local machine a `.githooks` directory
```shell
> mkdir -p .githooks
# create the hook script
> touch .githooks/post-receive
```
open the file in your favorite IDE and paste the content from the hook into it.
Then make it executable again
```shell
> chmod +x .githooks/post-receive
```
Then we commit and push the changes
```shell
> git add .githooks/post-receive
> git commit -m "add remote hooks"
> git push
```

### 2. Remote configuration
To tell the remote repo about those hooks we first `ssh` into the Pi
```shell
> ssh pi@10.0.0.2
# move to the remote repo
> cd $HOME/remote/myproject.git
```
Then point the `core.hooksPath` to our newly added `.githooks` directory inside the "CI/CD" folder
```shell
> git config core.hooksPath $HOME/work/myproject/.githooks
```

With that in place, please be aware of two things.

1. The hooks themselves lag behind, meaning when we push the previous code for the hook is executed and only on the next push we run an updated version. This might introduce issues that could be resolved by checking if there are changes to the hook that is currently being executed, then spawning a `subshell`. But I didn't want to dive that deep.
2. **Security Warning!** By doing this, you are effectively allowing *Remote Code Execution* (RCE) via `git push`. Anyone who gains access to your laptop or your `git` repository can modify the `post-receive` script to run malicious commands (like crypto miners or reverse shells) on your RaspberryPi simply by pushing code. Ensure your SSH connection is secure, you are using secure SSH keys AND your RaspberryPi is not exposing anything to the public internet. 

## Wrap-Up
Amazing, now I have a tiny CI and port everything to my Rust project!

Which I simultaniously did :)

Look at it's glory!!

```shell
> git add -p
diff --git a/.githooks/post-receive b/.githooks/post-receive
index 3475ecf..c2e469c 100755
--- a/.githooks/post-receive
+++ b/.githooks/post-receive
@@ -21,7 +21,7 @@ do
         cd $TARGET_DIR
 
         echo "--- deploy: Running Tests ---"
-        python script.py
+        cargo test
 
         echo "--- deploy: Complete! ---"
     else
(1/1) Stage this hunk [y,n,q,a,d,e,p,P,?]? a

> git commit -m "update post-receive"
[master da41dc7] update post-receive
 1 file changed, 1 insertion(+), 1 deletion(-)
> git push
pi@10.0.0.2's password: 
Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 12 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (4/4), 371 bytes | 371.00 KiB/s, done.
Total 4 (delta 2), reused 0 (delta 0), pack-reused 0 (from 0)
remote: --- deploy: Starting CI/CD for master ---
remote: Already on 'master'
remote: --- deploy: Running Tests ---
remote: python: can't open file '/home/pi/work/integers/script.py': [Errno 2] No such file or directory
remote: --- deploy: Complete! ---
To 10.0.0.2:remote/integers
   edff745..da41dc7  master -> master
```

Brilliant, here is the lag! =D

One last try...
```shell
> git commit -m "update tests"
[master 0a2f0d1] update tests
 1 file changed, 16 deletions(-)
> git push
pi@10.0.0.2's password: 
Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 12 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 354 bytes | 354.00 KiB/s, done.
Total 4 (delta 2), reused 0 (delta 0), pack-reused 0 (from 0)
remote: --- deploy: Starting CI/CD for master ---
remote: Already on 'master'
remote: --- deploy: Running Tests ---
remote:    Compiling integers v0.1.0 (/home/pi/work/integers)
remote: error[E0658]: use of unstable library feature `stdarch_neon_dotprod`
remote:    --> src/lib.rs:120:27
remote:     |
remote: 120 |                 sum_vec = vdotq_s32(sum_vec, va, vb);
remote:     |                           ^^^^^^^^^
remote:     |
remote:     = note: see issue #117224 <https://github.com/rust-lang/rust/issues/117224> for more information
remote: 
remote: warning[E0133]: call to unsafe function `std::arch::aarch64::vdupq_n_s32` is unsafe and requires unsafe block
remote:    --> src/lib.rs:111:31
remote:     |
remote: 111 |             let mut sum_vec = vdupq_n_s32(0);
remote:     |                               ^^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: note: an unsafe function restricts its caller, but its body is safe by default
remote:    --> src/lib.rs:102:9
remote:     |
remote: 102 |         pub unsafe fn dot_product_neon_raw(a: &[i8], b: &[i8]) -> i32 {
remote:     |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
remote:     = note: `#[warn(unsafe_op_in_unsafe_fn)]` on by default
remote: 
remote: warning[E0133]: call to unsafe function `std::arch::aarch64::vld1q_s8` is unsafe and requires unsafe block
remote:    --> src/lib.rs:117:26
remote:     |
remote: 117 |                 let va = vld1q_s8(ptr_a);
remote:     |                          ^^^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: 
remote: warning[E0133]: call to unsafe function `std::arch::aarch64::vld1q_s8` is unsafe and requires unsafe block
remote:    --> src/lib.rs:118:26
remote:     |
remote: 118 |                 let vb = vld1q_s8(ptr_b);
remote:     |                          ^^^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: 
remote: warning[E0133]: call to unsafe function `std::arch::aarch64::vdotq_s32` is unsafe and requires unsafe block
remote:    --> src/lib.rs:120:27
remote:     |
remote: 120 |                 sum_vec = vdotq_s32(sum_vec, va, vb);
remote:     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: 
remote: warning[E0133]: call to unsafe function `std::ptr::const_ptr::<impl *const T>::add` is unsafe and requires unsafe block
remote:    --> src/lib.rs:122:25
remote:     |
remote: 122 |                 ptr_a = ptr_a.add(16);
remote:     |                         ^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: 
remote: warning[E0133]: call to unsafe function `std::ptr::const_ptr::<impl *const T>::add` is unsafe and requires unsafe block
remote:    --> src/lib.rs:123:25
remote:     |
remote: 123 |                 ptr_b = ptr_b.add(16);
remote:     |                         ^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: 
remote: warning[E0133]: call to unsafe function `std::arch::aarch64::vaddvq_s32` is unsafe and requires unsafe block
remote:    --> src/lib.rs:125:13
remote:     |
remote: 125 |             vaddvq_s32(sum_vec)
remote:     |             ^^^^^^^^^^^^^^^^^^^ call to unsafe function
remote:     |
remote:     = note: for more information, see <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html>
remote:     = note: consult the function's documentation for information on how to avoid undefined behavior
remote: 
remote: Some errors have detailed explanations: E0133, E0658.
remote: For more information about an error, try `rustc --explain E0133`.
remote: warning: `integers` (lib) generated 7 warnings
remote: error: could not compile `integers` (lib) due to 1 previous error; 7 warnings emitted
remote: warning: build failed, waiting for other jobs to finish...
remote: warning: `integers` (lib test) generated 7 warnings (7 duplicates)
remote: error: could not compile `integers` (lib test) due to 1 previous error; 7 warnings emitted
remote: --- deploy: Complete! ---
To 10.0.0.2:remote/integers
   da41dc7..0a2f0d1  master -> master
```
Great, just as broken as it's supposed to be! =)
