import os
from bot import ReactionsHelper


def main():
    bot = ReactionsHelper(prefix='$', filename='data.json', processing_reaction='⏳')
    bot.run(os.getenv('ReactionHelperToken'))


if __name__ == '__main__':
    main()
