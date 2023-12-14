"""
Module of rates' repository CRUD
"""

from pydantic import UUID4
from sqlalchemy import select, and_, desc, func
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.models import Rate, User, Image
from src.schemas.rates import RateModel, RateImageResponse


async def read_all_rates_to_photo(
    image_id: UUID4 | int,
    offset: int,
    limit: int,
    session: AsyncSession) -> list[Rate] | None:

    stmt = select(Rate).filter(Rate.image_id == image_id)
    stmt = stmt.order_by(desc(Rate.created_at))
    stmt = stmt.offset(offset).limit(limit)
    rates = await session.execute(stmt)

    return rates.scalars()

async def read_avg_rate_to_photo(
    image_id: UUID4 | int,
    session: AsyncSession) -> float | None:
    
    stmt = select(func.avg(Rate.rate)).where(Rate.image_id == image_id)
    avg_rate = await session.execute(stmt)

    return RateImageResponse(avg_rate=avg_rate.scalar(), image_id=image_id)

async def read_all_avg_rate(session: AsyncSession):
    stmt = select(Image.id, func.coalesce(func.avg(Rate.rate),0).label("average_rate")
                  ).join(Rate, Image.id == Rate.image_id, isouter=True)\
                   .group_by(Image.id)\
                    .order_by(func.avg(Rate.rate).desc().nulls_last())
    avg_rates = await session.execute(stmt)
    avg_rates = avg_rates.all()
    
    return [RateImageResponse(avg_rate=avg_rate, image_id=image_id) for image_id, avg_rate in avg_rates]

async def create_rate_to_photo(
    image_id: UUID4 | int,
    body: RateModel,
    user: User,
    session: AsyncSession) -> Rate | None:
    photo = await session.get(Image, image_id)
    if photo and photo.user_id != user.id:
        stmt = select(Rate).filter(
        and_(Rate.image_id == image_id, Rate.user_id == user.id)
        )
        rate = await session.execute(stmt)
        rate = rate.scalar()
        if not rate :
            rate_photo = Rate(image_id=image_id,
                      rate=body.rate,
                      user_id=user.id)
            session.add(rate_photo)
            await session.commit()
            await session.refresh(rate_photo)
            return rate_photo
    return None


async def delete_rate_to_photo(
    rate_id: UUID4 | int,
    session: AsyncSession
) -> Rate | None:
    stmt = select(Rate).filter(Rate.id == rate_id)
    rate = await session.execute(stmt)
    rate = rate.scalar()
    if rate:
        await session.delete(rate)
        await session.commit()
    return rate
