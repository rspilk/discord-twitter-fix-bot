# discord-twitter-fix-bot
This is a discord bot designed to fix the way discord presents tweets

Some features are:

## Text expansion
Discord doesnt render the full text sometimes when the tweet exceeds some amount of characters. It will respond with the full text content when it is detected


## Gallery Exapansion
Discord will only display the first image of a gallery. When the bot detects more images it will expand the gallery and post all the links to images which will be displayed in preview.

## Comment and retweet context
When a retweet is detected, the context tweet link will be posted to provide context. Also comment threads will respond with the parent comment and the root tweet that the thread is contained in. This will be neglected if the commenter or root parent is the same to avoid live-tweet events.
