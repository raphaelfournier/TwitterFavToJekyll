# TwitterFavToJekyll

Retrieve your Twitter favorites and save them to a directory for a Jekyll site.
You may choose to delete them.

The point is to collect regularly Twitter favorites and store them outside the
platform (for backup purposes). The Jekyll aspect enables quick visualisation
and sorting if necessary (could be optimized though).

Before any usage, it is required to create a Twitter application and fill the
given access tokens in a config file. See
[https://dev.twitter.com/oauth/overview/introduction]() for an introduction to
using OAuth with the Twitter API.

# Usage

    python saveTweetsToJekyll.py [-h] [-p | -o <filename>] [-r] [-d] [-f <folder>] [-c <configfile>]

optional arguments:

    -h, --help                               show help message and exit
    -p, --processAll                         process all data files from current folder
    -o <filename>, --processOne <filename>   process one file from current folder
    -r, --retrieve                           retrieve tweets from Twitter
    -d, --delete                             delete the tweets on Twitter
    -f <folder>, --folder <folder>           specify Jekyll root folder
    -c <configfile>, --config <configfile>   select a config file

# Demo

An old and not pretty version is available at [http://favoris.fournier-sniehotta.fr]().

# TODO

- Publish the code of the Jekyll site used in the demo
