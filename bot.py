# coding: utf-8
import time
import os
import logging
import praw
import re
from config import *


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(asctime)s - %(message)s')
# logging.disable(logging.CRITICAL)


def auth():
    logging.info("Authenticating...")
    reddit = praw.Reddit('OnReddit', user_agent=USER_AGENT)
    logging.info("Authenticated as {}".format(reddit.user.me()))
    return reddit


def process_submission(reddit, submission):
    title = submission.title  # Submission's title
    url = submission.url  # Submission's url
    xpost = "[r/{}] ".format(submission.subreddit.display_name)  # x-post string: [r/subreddit]
    source_url = 'https://www.reddit.com' + submission.permalink  # link to submission's comment section


    new_post_title = xpost + title

    if len(new_post_title) > 293: # if title is greater than 300 (title limit) minus NSFW flag (7)
        new_post_title = new_post_title[0:290] + '...' # substring 290 chars and add ellipsis, leaving NSFW space

    if submission.over_18:
        new_post_title += ' | NSFW'

    new_post_url = url
    post_to = reddit.subreddit(SUBREDDIT_TO_POST)

    new_post(post_to, new_post_title, new_post_url, source_url)
    logging.info(new_post_title)


def new_post(subreddit, title, url, source_url):
    logging.info(title)
    if POST_MODE == 'direct':
        post = subreddit.submit(title, url=url)
        comment_text = "[Link to original post here]({})".format(source_url)
        post.reply(comment_text).mod.distinguish(sticky=True)

    elif POST_MODE == 'comment':
        subreddit.submit(title, url=source_url)

    else:
        logging.ERROR('Invalid POST_MODE chosen. Select "direct" or "comment".')


def monitor(reddit, submissions_found):
    counter = 0
    with open('submissions_processed.txt', 'a') as f:
        for submission in reddit.subreddit(SUBREDDITS_TO_MONITOR).hot(limit=SEARCH_LIMIT):
            logging.debug(u'Submission: {}'.format(submission.title))
            for expression in EXPRESSIONS_TO_MONITOR:
                expression = re.compile(expression, re.I) # Ignore case
                if expression.match(submission.title) and submission.id not in submissions_found:
                    logging.info(u'Found it! {}'.format(submission.title))
                    process_submission(reddit, submission)
                    submissions_found.append(submission.id)
                    counter += 1
                    f.write(submission.id)    

    logging.info(str(counter) + ' submission(s) found')  # log results

    # Sleep for a few minutes
    logging.info('Waiting...')  # log results
    time.sleep(WAIT_TIME*60)


def get_submissions_processed():
    if not os.path.isfile('submissions_processed.txt'):
        submissions_processed = []
    else:
        with open('submissions_processed.txt', 'r') as f:
            submissions_processed = f.read()
            submissions_processed = submissions_processed.split('\n')

    return submissions_processed


def main():
    logging.info('Reddit bot running...')
    # Authentication
    reddit = auth()
    # Monitor Reddit for new submissions
    submissions_found = get_submissions_processed()
    while True:
        try:
            monitor(reddit, submissions_found)
        except Exception as e:
            logging.warning("Random exception occurred: {}".format(e))
            time.sleep(WAIT_TIME * 60)


if __name__ == '__main__':
    main()
