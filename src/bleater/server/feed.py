from bleater.models.posts import Post
from bleater.server.storage import BaseStorage
import datetime

# TODO allow different feed algorithms


async def get_feed(storage: BaseStorage) -> list[Post]:
    ts = int(datetime.datetime.now().timestamp())
    recent = await storage.get_last_posts(500)
    if len(recent) == 0:
        return []

    earliest = recent[-1].timestamp
    ts_span = ts - earliest

    weighted = [(_post_weight(ts, post, ts_span), Post) for post in recent]
    recent.sort(key=lambda a: _post_weight(ts, a, ts_span), reverse=True)
    return recent[:10]


def _post_weight(now: int, post: Post, ts_span: int) -> int:
    # We assume it's never 0 ;)
    td = now - post.timestamp
    if td > 0:
        tw = ts_span // td
    else:
        tw = ts_span
    return tw + (post.replies or 0)
