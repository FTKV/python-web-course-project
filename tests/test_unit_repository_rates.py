from datetime import datetime
import unittest
import pickle

from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio.client import Redis

from src.database.models import Rate, User, Image
from src.schemas.rates import RateModel, RateImageResponse
from src.repository.rates import (
    read_all_rates_to_image,
    read_all_my_rates,
    read_all_user_rates,
    read_avg_rate_to_image,
    read_all_avg_rates,
    create_rate_to_image,
    delete_rate_to_image
)


class TestComments(unittest.IsolatedAsyncioTestCase):
    image_id = 1
    rates = [
            Rate(id=1, rate = 4 , user_id=1, image_id=1),
            Rate(id=2, rate = 5, user_id=2, image_id=1)
        ]
    
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        #self.session = MagicMock(spec=AsyncSession)
        self.user = User(id=1)
        self.rate = Rate(
            rate = 5,
            user_id = 1,
            image_id = 1,
            id = 1,
        )
        self.body = RateModel(
            rate=3
        )
        self.cache = AsyncMock(spec=Redis)
        self.test_image = Image(id=1, url="http://example.com", user_id=1)
        self.serialized_image = pickle.dumps(self.test_image)
        self.read_image_mock = AsyncMock(return_value=self.test_image)
        
        self.avg_rate_result = AsyncMock()
        self.avg_rate_result.scalar.return_value = 4.5
        self.session.execute.return_value = self.avg_rate_result
        self.cache.get.return_value = self.serialized_image
        
    async def test_read_all_rates_to_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.rates
        result = await read_all_rates_to_image(
            image_id=1,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.rates)
            
    async def test_read_all_my_rates(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.rates
        result = await read_all_my_rates(
            user = self.user,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.rates)
        
    async def test_read_all_user_rates(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.rates
        result = await read_all_user_rates(
            user_id = self.user.id,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.rates)
    

    async def test_create_rate_to_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        result = await create_rate_to_image(
            image_id=self.rate.image_id, body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result.rate, self.body.rate)
        self.assertEqual(result.image_id, self.rate.image_id)
        self.assertEqual(result.user_id, self.rate.user_id)
        self.assertTrue(hasattr(result, "id"))
   
    async def test_delete_rate_to_photo(self):
        rate = Rate()
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = rate
        result = await delete_rate_to_image(
            rate_id=rate.id, session=self.session
        )
        self.assertEqual(result, rate)
        