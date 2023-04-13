import pymongo
import json
from lib.logging_utils import init_logger
from settings import MONGODB_URL
from datetime import datetime
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
logger = init_logger(__name__)


default_options = {"name": "mongo", "database":"conserver", "collection_name":"vcons"}

def prepare_vcon_for_mongo(vcon: dict) -> dict:
    clean_vcon = json.loads(vcon.dumps())
    clean_vcon['_id'] = vcon.uuid
    clean_vcon['created_at'] = datetime.fromisoformat(clean_vcon['created_at'])
    for dialog in clean_vcon['dialog']:
        dialog['start'] = datetime.fromisoformat(dialog['start'])
    return clean_vcon


async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the mongo storage")
    client = pymongo.MongoClient(MONGODB_URL)
    try:
        # Cannot create redis client in global context as it may get wait on async 
        # event loop which may go away.
        vcon_redis = VconRedis()
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        db = client[opts['database']]
        collection = db[opts['collection']]
        # upsert this vCon
        results = collection.update_one(
            {"_id": vcon_uuid},
            {"$set": prepare_vcon_for_mongo(vcon)},
            upsert=True
        )
        logger.info(f"mongo storage plugin: inserted vCon: {vcon_uuid}, results: {results} ")
    except Exception as e:
        logger.error(f"mongo storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
        raise e

