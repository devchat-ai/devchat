from typing import List, Optional

from fastapi import APIRouter, Query

from devchat._service.schema import request, response
from devchat.msg.topic_util import delete_topic as del_topic
from devchat.msg.topic_util import get_topic_shortlogs, get_topics

router = APIRouter()

@router.get("/{topic_root_hash}/logs", response_model=List[response.ShortLog])
async def get_topic_logs(
    topic_root_hash: str,
    limit: int = Query(1, gt=0, description="maximum number of records to return"),
    offset: int = Query(0, ge=0, description="offset of the first record to return"),
    workspace: Optional[str] = Query(None, description="absolute path to the workspace/repository"),
):
    # TODO: handle error in the http way
    records, error = get_topic_shortlogs(topic_root_hash, limit, offset, workspace)

    logs = [response.ShortLog.parse_obj(record) for record in records]
    return logs


@router.get("", response_model=List[response.TopicSummary])
def list_topics(
    limit: int = Query(1, gt=0, description="maximum number of records to return"),
    offset: int = Query(0, ge=0, description="offset of the first record to return"),
    workspace: Optional[str] = Query(None, description="absolute path to the workspace/repository"),
):
    topics = get_topics(
        limit=limit,
        offset=offset,
        workspace_path=workspace,
        with_deleted=False,
    )

    summaries = [
        response.TopicSummary(
            latest_time=topic["latest_time"],
            title=topic["title"],
            hidden=topic["hidden"],
            root_prompt_hash=topic["root_prompt"]["hash"],
            root_prompt_user=topic["root_prompt"]["user"],
            root_prompt_date=topic["root_prompt"]["date"],
            root_prompt_request=topic["root_prompt"]["request"],
            root_prompt_response=topic["root_prompt"]["responses"][0],
        )
        for topic in topics
    ]
    return summaries


@router.post("/delete", response_model=response.DeleteTopic)
def delete_topic(
    item: request.DeleteTopic,
):
    print(f"check delete topic request: \n{item}")
    try:
        del_topic(item.topic_hash, item.workspace)
        return response.DeleteTopic(topic_hash=item.topic_hash, success=True)
    except Exception as e:
        return response.DeleteTopic(
            topic_hash=item.topic_hash,
            success=False,
            error=str(e),
        )
