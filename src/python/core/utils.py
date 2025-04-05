from typing import List


def paginate(queryset: List, page=1, limit=25):
    start = (page - 1) * limit
    end = start + limit
    return queryset[start:end]