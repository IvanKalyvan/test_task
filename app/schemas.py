from pydantic import BaseModel

class Post_Schema(BaseModel):

    title: str
    content: str
    user_id: int

class CommentSchema(BaseModel):

    content: str
    post_id: int