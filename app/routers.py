import io

from fastapi import APIRouter, HTTPException, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
from PyPDF2 import PdfReader

from fastapi_users_local import fastapi_users
from pg_functions.database_connect import User, get_async_session
from pg_functions.models import post, comment
from schemas import Post_Schema
from gpt_management.gpt_utils import create_tasks_for_gpt

post_router = APIRouter(

    prefix="/posts",
    tags=["Posts"]

)

current_active_verified_user = fastapi_users.current_user(active=True, verified=True)

@post_router.get("/get/my-posts")
async def get_all_private_posts_id(

        user: User = Depends(current_active_verified_user),
        session: AsyncSession = Depends(get_async_session)

):

    try:

        query = select(post).where(post.c.user_id == user.id)
        result = await session.execute(query)
        result = result.all()

        return [id[0] for id in result]

    except:

        raise HTTPException(

            status_code=404,
            headers={'404': 'Record not found!'}

        )

@post_router.get("/get")
async def get_all_posts_id(

        session: AsyncSession = Depends(get_async_session)

):

    try:

        query = select(post)
        result = await session.execute(query)
        result = result.all()

        return [id[0] for id in result]

    except:

        raise HTTPException(

            status_code=404,
            headers={'404': 'Record not found!'}

        )

@post_router.get("/get/{post_id}")
async def get_post_by_id(

        post_id: int,
        session: AsyncSession = Depends(get_async_session)

                    ):

    try:

        query = select(post).where(post.c.id == post_id)
        result = await session.execute(query)
        result = result.all()

        return {

            "title": result[0][1],
            "content": result[0][2],

        }

    except:

        raise HTTPException(

            status_code=404,
            headers={'404': 'Record not found!'}

        )

@post_router.post("/post")
async def post_post(

        post_info: Post_Schema,
        user: User = Depends(current_active_verified_user),
        session: AsyncSession = Depends(get_async_session)

):

    try:

        params = []

        post_info.user_id = user.id
        post_info = post_info.dict()

        for item in post_info:

            if item != "user_id":

                params.append({f'{item}': f'{post_info[item]}'})

            if item in ("title", "content"):

                if (len(post_info[item]) < 5 and item == "title") or (len(post_info[item]) < 20 and item == "content"):

                    raise HTTPException(

                        status_code=422,
                        detail={'422': f'Missed field ({item})'},
                        headers={'422': f'Missed field ({item})'}

                    )

        results = await create_tasks_for_gpt(params)

        for validate in results:

            if validate["answer"] == "good":

                pass

            else:

                raise HTTPException(

                    status_code=422,
                    detail={'422': f'{validate["answer"]}'},
                    headers={'422': f'{validate["answer"]}'}
                )

        stmt = insert(post).values(**post_info)
        await session.execute(stmt)
        await session.commit()

        return {'201': 'successful'}

    except Exception as e:

        print(e)

        return e

@post_router.delete("/delete/{post_id}")
async def delete_post(

        post_id: int,
        user: User = Depends(current_active_verified_user),
        session: AsyncSession = Depends(get_async_session)

):

    try:

        stmt = delete(post).where(post.c.id == post_id, post.c.user_id == user.id)
        await session.execute(stmt)
        await session.commit()

        return HTTPException(

            status_code=204,
            headers={'204': 'Successful delete!'}

        )

    except:

        raise HTTPException(

            status_code=404,
            headers={'404': 'Record not found!'}

        )

@post_router.put("/put/{post_id}")
async def put_post(

        post_id: int,
        post_info: Post_Schema,
        user: User = Depends(current_active_verified_user),
        session: AsyncSession = Depends(get_async_session)

):
    try:

        params = []

        post_info.user_id = user.id
        post_info = post_info.dict()

        for item in post_info:

            if item != "user_id":
                params.append({f'{item}': f'{post_info[item]}'})

            if item in ("title", "content"):

                if (len(post_info[item]) < 5 and item == "title") or (
                        len(post_info[item]) < 20 and item == "content"):
                    raise HTTPException(

                        status_code=422,
                        detail={'422': f'Missed field ({item})'},
                        headers={'422': f'Missed field ({item})'}

                    )

        results = await create_tasks_for_gpt(params)

        for validate in results:

            if validate["answer"] == "good":

                pass

            else:

                raise HTTPException(

                    status_code=422,
                    detail={'422': f'{validate["answer"]}'},
                    headers={'422': f'{validate["answer"]}'}
                )

        stmt = update(post).where(post.c.id == post_id, post.c.user_id == user.id).values(**post_info)
        await session.execute(stmt)
        await session.commit()

        return {'201': 'successful'}

    except Exception as e:

        raise e

@post_router.patch("/patch/{post_id}")
async def patch_post(

        post_id: int,
        post_info: Post_Schema,
        user: User = Depends(current_active_verified_user),
        session: AsyncSession = Depends(get_async_session)

):
    try:

        params = []
        skipped_params = []

        post_info.user_id = user.id
        post_info = post_info.dict()

        for item in post_info:

            if item != "user_id":

                params.append({f'{item}': f'{post_info[item]}'})

            if item in ("title", "content"):

                if ((len(post_info[item]) < 5 and item == "title") or (len(post_info[item]) < 20 and item == "content")) \
                        and len(post_info[item]) != 0:

                    raise HTTPException(

                        status_code=422,
                        detail={'422': f'Missed field ({item})'},
                        headers={'422': f'Missed field ({item})'}

                    )

                if len(post_info[item]) == 0:

                    skipped_params.append(item)

        results = await create_tasks_for_gpt(params)

        for param in skipped_params:

            del post_info[param]

        for validate in results:

            if validate["answer"] == "good":

                pass

            else:

                raise HTTPException(

                    status_code=422,
                    detail={'422': f'{validate["answer"]}'},
                    headers={'422': f'{validate["answer"]}'}
                )

        stmt = update(post).where(post.c.id == post_id, post.c.user_id == user.id).values(**post_info)
        await session.execute(stmt)
        await session.commit()

        return {'201': 'successful'}

    except Exception as e:

        raise e

#
# comment_router = APIRouter(
#
#     prefix="/comments",
#     tags=["Comments"]
#
# )
#
# @post_router.get("/get/my-comments")
# async def get_all_private_comments_id(
#
#         user: User = Depends(current_active_verified_user),
#         session: AsyncSession = Depends(get_async_session)
#
# ):
#
#     try:
#
#         query = select(comment).where(comment.c.user_id == user.id)
#         result = await session.execute(query)
#         result = result.all()
#
#         return [id[0] for id in result]
#
#     except:
#
#         raise HTTPException(
#
#             status_code=404,
#             headers={'404': 'Record not found!'}
#
#         )
#
# @post_router.get("/get")
# async def get_all_comments_id(
#
#         session: AsyncSession = Depends(get_async_session)
#
# ):
#
#     try:
#
#         query = select(comment)
#         result = await session.execute(query)
#         result = result.all()
#
#         return [id[0] for id in result]
#
#     except:
#
#         raise HTTPException(
#
#             status_code=404,
#             headers={'404': 'Record not found!'}
#
#         )
#
# @post_router.get("/get/{comment_id}")
# async def get_comment_by_id(
#
#         comment_id: int,
#         session: AsyncSession = Depends(get_async_session)
#
#                     ):
#
#     try:
#
#         query = select(comment).where(comment.c.id == comment_id)
#         result = await session.execute(query)
#         result = result.all()
#
#         return {
#
#             "title": result[0][1],
#             "content": result[0][2],
#
#         }
#
#     except:
#
#         raise HTTPException(
#
#             status_code=404,
#             headers={'404': 'Record not found!'}
#
#         )
#
# @post_router.post("/post")
# async def post_post(
#
#         post_info: Post_Schema,
#         user: User = Depends(current_active_verified_user),
#         session: AsyncSession = Depends(get_async_session)
#
# ):
#
#     try:
#
#         params = []
#
#         post_info.user_id = user.id
#         post_info = post_info.dict()
#
#         for item in post_info:
#
#             if item != "user_id":
#
#                 params.append({f'{item}': f'{post_info[item]}'})
#
#             if item in ("title", "content"):
#
#                 if (len(post_info[item]) < 5 and item == "title") or (len(post_info[item]) < 20 and item == "content"):
#
#                     raise HTTPException(
#
#                         status_code=422,
#                         detail={'422': f'Missed field ({item})'},
#                         headers={'422': f'Missed field ({item})'}
#
#                     )
#
#         results = await create_tasks_for_gpt(params)
#
#         for validate in results:
#
#             if validate["answer"] == "good":
#
#                 pass
#
#             else:
#
#                 raise HTTPException(
#
#                     status_code=422,
#                     detail={'422': f'{validate["answer"]}'},
#                     headers={'422': f'{validate["answer"]}'}
#                 )
#
#         stmt = insert(post).values(**post_info)
#         await session.execute(stmt)
#         await session.commit()
#
#         return {'201': 'successful'}
#
#     except Exception as e:
#
#         print(e)
#
#         return e
#
# @post_router.delete("/delete/{comment_id}")
# async def delete_post(
#
#         comment_id: int,
#         user: User = Depends(current_active_verified_user),
#         session: AsyncSession = Depends(get_async_session)
#
# ):
#
#     try:
#
#         stmt = delete(post).where(post.c.id == post_id, post.c.user_id == user.id)
#         await session.execute(stmt)
#         await session.commit()
#
#         return HTTPException(
#
#             status_code=204,
#             headers={'204': 'Successful delete!'}
#
#         )
#
#     except:
#
#         raise HTTPException(
#
#             status_code=404,
#             headers={'404': 'Record not found!'}
#
#         )
#
# @post_router.put("/put/{comment_id}")
# async def put_post(
#
#         comment_id: int,
#         post_info: Post_Schema,
#         user: User = Depends(current_active_verified_user),
#         session: AsyncSession = Depends(get_async_session)
#
# ):
#     try:
#
#         params = []
#
#         post_info.user_id = user.id
#         post_info = post_info.dict()
#
#         for item in post_info:
#
#             if item != "user_id":
#                 params.append({f'{item}': f'{post_info[item]}'})
#
#             if item in ("title", "content"):
#
#                 if (len(post_info[item]) < 5 and item == "title") or (
#                         len(post_info[item]) < 20 and item == "content"):
#                     raise HTTPException(
#
#                         status_code=422,
#                         detail={'422': f'Missed field ({item})'},
#                         headers={'422': f'Missed field ({item})'}
#
#                     )
#
#         results = await create_tasks_for_gpt(params)
#
#         for validate in results:
#
#             if validate["answer"] == "good":
#
#                 pass
#
#             else:
#
#                 raise HTTPException(
#
#                     status_code=422,
#                     detail={'422': f'{validate["answer"]}'},
#                     headers={'422': f'{validate["answer"]}'}
#                 )
#
#         stmt = update(post).where(post.c.id == post_id, post.c.user_id == user.id).values(**post_info)
#         await session.execute(stmt)
#         await session.commit()
#
#         return {'201': 'successful'}
#
#     except Exception as e:
#
#         raise e
#
# @post_router.patch("/patch/{comment_id}")
# async def patch_post(
#
#         comment_id: int,
#         post_info: Post_Schema,
#         user: User = Depends(current_active_verified_user),
#         session: AsyncSession = Depends(get_async_session)
#
# ):
#     try:
#
#         params = []
#         skipped_params = []
#
#         post_info.user_id = user.id
#         post_info = post_info.dict()
#
#         for item in post_info:
#
#             if item != "user_id":
#
#                 params.append({f'{item}': f'{post_info[item]}'})
#
#             if item in ("title", "content"):
#
#                 if ((len(post_info[item]) < 5 and item == "title") or (len(post_info[item]) < 20 and item == "content")) \
#                         and len(post_info[item]) != 0:
#
#                     raise HTTPException(
#
#                         status_code=422,
#                         detail={'422': f'Missed field ({item})'},
#                         headers={'422': f'Missed field ({item})'}
#
#                     )
#
#                 if len(post_info[item]) == 0:
#
#                     skipped_params.append(item)
#
#         results = await create_tasks_for_gpt(params)
#
#         for param in skipped_params:
#
#             del post_info[param]
#
#         for validate in results:
#
#             if validate["answer"] == "good":
#
#                 pass
#
#             else:
#
#                 raise HTTPException(
#
#                     status_code=422,
#                     detail={'422': f'{validate["answer"]}'},
#                     headers={'422': f'{validate["answer"]}'}
#                 )
#
#         stmt = update(post).where(post.c.id == post_id, post.c.user_id == user.id).values(**post_info)
#         await session.execute(stmt)
#         await session.commit()
#
#         return {'201': 'successful'}
#
#     except Exception as e:
#
#         raise e

pdf_file_router = APIRouter(

    prefix='/summarize',
    tags=['Summarize']

)

@pdf_file_router.post("/")
async def create_summary(

    file: UploadFile | None = None

):

    if file.content_type != "application/pdf":

        raise HTTPException(status_code=400, detail="File must be in .pdf format")

    contents = await file.read()

    pdf_reader = PdfReader(io.BytesIO(contents))
    num_pages = len(pdf_reader.pages)

    if num_pages > 1:

        raise HTTPException(status_code=400, detail="PDF must have not more than 1 page!")

    page = pdf_reader.pages[0]
    text = page.extract_text()

    results = await create_tasks_for_gpt([{"text": text}])

    return {"summary": f"{results[0]['summary']}"}