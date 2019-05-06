import discord, re
import tweepy
import json
import datetime

# Discord
client_token = ''

# Twitter
consumer_key=''
consumer_secret=''
access_token_key=''
access_token_secret=''

tweet_context_depth = 1

class MyClient(discord.Client):
    def is_twitter_link(self, msgText):
        regex = r"http(?:s)?:\/\/(?:www\.)?twitter\.com\/([a-zA-Z0-9_]+)\/?status\/([0-9]+)"
        matches = re.search(regex, msgText)
        if matches:
            twitterID = matches.groups()[1]
            return [True, twitterID]
        else:
            return [False]
    def check_comment(self, tweet):
        try:
            if 'in_reply_to_status_id' in tweet and tweet['in_reply_to_status_id'] != None and tweet['in_reply_to_screen_name'] != tweet['user']['screen_name']:
                return True
        except:
            return False


    def check_retweet(self, tweet):
        try:
            if 'quoted_status_id' in tweet:
                return True
        except:
            return False


    def get_tweet_text(self, tweet):
        return tweet['full_text']


    def get_tweet_user(self, tweet):
        return tweet['user']['screen_name']


    def get_tweet_id(self, tweet):
        return tweet['id']


    def get_tweet(self, twitterID):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token_key, access_token_secret)
        api = tweepy.API(auth)
        tweet = api.get_status(twitterID, tweet_mode='extended')._json
        return tweet


    def get_timestamp(self):
        ts = datetime.datetime.now().timestamp()
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


    # returns true if 2 or more
    def has_images(self, tweet):
        if 'extended_entities' in tweet and 'media' in tweet['extended_entities'] and len(tweet['extended_entities']['media']) > 1:
            return [True,[i['media_url_https'] for i in tweet['extended_entities']['media']]]
        else:
            return [False]

    def has_url(self, tweet):
        if 'extended_entities' in tweet and 'urls' in tweet['extended_entities'] and len(tweet['extended_entities']['urls']) > 0:
            return [True,[i['expanded_url'] for i in tweet['extended_entities']['urls']]]
        else:
            return [False]

    def tweet_too_long(self, tweet):
        if len(tweet['full_text']) > 268:
            return True
        else:
            return False


    def tweet_type_check(self,tweet):
        if self.check_comment(tweet):
            return 'comment'
        if self.check_retweet(tweet):
            return 'retweet'
        else:
            return 'root'


    def get_parent(self,tweet):
        tweet_type = self.tweet_type_check(tweet)
        print(tweet_type)
        if tweet_type == 'comment':
            return self.get_comment_parent(tweet)
        if tweet_type == 'retweet':
            return self.get_retweet_parent(tweet)
        if tweet_type == 'root':
            # if it doesnt have those two variables it must be root
            #print("something went wrong in get_parent")
            return False
        else:
            print("Something went wrong in get_parent")
            return False

    def get_comment_parent(self, tweet):
        parentID = tweet['in_reply_to_status_id']
        parent = self.get_tweet(parentID)
        print("\t%s\t%s\t%s" % (self.get_tweet_id(parent), self.get_tweet_user(parent), self.get_tweet_text(parent)))
        return parent

    def get_retweet_parent(self, tweet):
        parentID = tweet['quoted_status_id']
        parent = self.get_tweet(parentID)
        print("\t%s\t%s\t%s" % (self.get_tweet_id(parent), self.get_tweet_user(parent), self.get_tweet_text(parent)))
        return parent


    def find_root_tweets(self, tweet):
        parents = []
        root_found = False
        i = 1
        while 1:
            parent_tweet = self.get_parent(tweet)
            if parent_tweet == False:
                return parents
            parents.append(parent_tweet)
            tweet = parent_tweet

    def logging_message(self,tweet):
        return "%s\t%s\t%s" % (self.get_timestamp(), self.get_tweet_user(tweet), self.get_tweet_text(tweet))    


    def too_long_message(self,tweet):
        return "Full Tweet by ***@%s***:\n```%s```" % (self.get_tweet_user(tweet), self.get_tweet_text(tweet))

    def parent_tweet_message(self, tweet, index):
        return "Index %s: Parent Tweet: \n https://twitter.com/%s/status/%s" % (index,self.get_tweet_user(tweet),self.get_tweet_id(tweet))

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        twitterCheck = self.is_twitter_link(message.content)
        if twitterCheck[0]:
            twitterID = twitterCheck[1]
            original_tweet = self.get_tweet(twitterID)
            # log message to console
            print(self.logging_message(original_tweet))
            check_images = self.has_images(original_tweet)
#TODO fix url parse
#            check_url = self.has_url(original_tweet)
            # Check if too long to fully display, if so print full text to chat
            if self.tweet_too_long(original_tweet):
                await message.channel.send(self.too_long_message(original_tweet))
            # Output the images if exist
            if check_images[0]:
                await message.channel.send("Multiple Images detected, expanding..")
                for img in check_images[1][1:]:
                    await message.channel.send(img)
#            if check_url[0]:
#                await message.channel.send("URL Detected, pasting")
#                for url in check_url[1]:
#                    await message.channel.send(url)
            # find root of all tweets
            tweet_chain = []
            tweet_chain = self.find_root_tweets(original_tweet)
            #testing
            #
            #for i in tweet_chain:
            #    print("https://twitter.com/%s/status/%s" % (self.get_tweet_user(i),self.get_tweet_id(i)))
            #tweet_chain.insert(0, original_tweet)
            # Only trigger if it is more than given tweet
            if tweet_chain != []:
                if len(tweet_chain) > tweet_context_depth+1:
                    # If chain is longer than tweet_context_depth, truncate to most recent desired context tweets and root tweet
                    tweet_chain = tweet_chain[:tweet_context_depth]+tweet_chain[1:]
                for idx,msg in enumerate(tweet_chain):
                    await message.channel.send(self.parent_tweet_message(msg,idx))
                    #await message.channel.send("https://twitter.com/%s/status/%s" % (self.get_tweet_user(msg),self.get_tweet_id(msg)))
                    print(self.parent_tweet_message(msg,idx))
                    # TODO : Fix expanding parent images
                    check_images = self.has_images(msg)
                    if check_images[0]:
                        await message.channel.send("Multiple Images detected, expanding..")
                        for img in check_images[1][:-1]:
                            print(img)
                            await message.channel.send(img)
        else:
            pass
        
client = MyClient()
client.run(client_token)
