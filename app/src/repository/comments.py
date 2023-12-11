"""
Module of comments' CRUD
"""

from pydantic import UUID4
from sqlalchemy import select, and_, desc
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.models import Comment, User
from src.schemas.comments import CommentModel


async def read_all_comments_to_photo(image_id: UUID4 | int, session: AsyncSession) -> list[Comment]:
    stmt = select(Comment)
    stmt = stmt.filter(
        and_(Comment.image_id == image_id, Comment.parent_id == None)
    )
    stmt = stmt.order_by(desc(Comment.created_at))
    comments = await session.execute(stmt)
    comments = comments.scalars().all()
    
    stmt_child = select(Comment)
    stmt_child = stmt_child.filter(
        and_(Comment.image_id == image_id, Comment.parent_id != None)
    )
    stmt_child = stmt_child.order_by(Comment.created_at)
    comments_child = await session.execute(stmt_child)
    comments_child = comments_child.scalars().all()
    
    
    for el_child in comments_child:
        for index, el_comment in enumerate(comments):
            if el_child.parent_id == el_comment.id:
                comments.insert(index, el_child)
                break
    
    return comments


async def create_comment_to_photo(image_id: UUID4 | int, body: CommentModel, user: User, session: AsyncSession) -> Comment | None:
    comment = Comment(image_id=image_id, text=body.text, user_id=user.id)
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


async def create_comment_to_comment(comment_id: UUID4 | int, body: CommentModel, user: User, session: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter(Comment.id == comment_id)
    parent_comment = await session.execute(stmt)
    parent_comment = parent_comment.scalar()
    if not parent_comment.parent_id:
        comment = Comment(image_id=parent_comment.image_id, text=body.text, user_id=user.id, parent_id=parent_comment.id)
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment
    return None

async def update_comment(comment_id: UUID4 | int, body: CommentModel, user: User, session: AsyncSession)-> Comment | None:
    stmt = select(Comment).filter(
        and_(Comment.id == comment_id, Comment.user_id == user.id)
    )
    comment = await session.execute(stmt)
    comment = comment.scalar()
    if comment:
        comment.text = body.text
        await session.commit()
    return comment

async def delete_comment(comment_id: UUID4 | int, user: User, session: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter(Comment.id == comment_id)
    comment = await session.execute(stmt)
    comment = comment.scalar()
    if comment:
        await session.delete(comment)
        await session.commit()
    return comment
    