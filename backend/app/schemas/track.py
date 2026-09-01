"""Musiqa trek sxemalari."""

from pydantic import BaseModel


class TrackRead(BaseModel):
    id: int
    original_name: str
    size_bytes: int
    sort_order: int
    # /media/music/{user_id}/{filename}
    url: str


class TracksResponse(BaseModel):
    tracks: list[TrackRead]
    total_bytes: int
    limit_bytes: int
    remaining_bytes: int
