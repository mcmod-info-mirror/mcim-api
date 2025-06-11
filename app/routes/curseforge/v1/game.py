"""
暂时不提供 game 相关的接口，优先级靠后
"""

# from fastapi import APIRouter
# from fastapi.responses import JSONResponse

# games_router = APIRouter(prefix="/games", tags=["games"])

# @games_router.get(
#     "/curseforge/games",
#     responses={
#         200: {
#             "description": "Curseforge Games info",
#             "content": {
#                 "application/json": {
#                     "example": {"status": "success", "data": [curseforge_game_example]}
#                 }
#             },
#         }
#     },
#     description="Curseforge 的全部 Game 信息",
#     tags=["Curseforge"],
# )
# async def curseforge_games():
#     with Session(bind=sql_engine) as session:
#         all_data = []
#         t = tables.curseforge_game_info
#         sql_games_result = session.query(t, t.c.time, t.c.status, t.c.data).all()
#         for result in sql_games_result:
#             if result is None or result == () or result[1] != 200:
#                 break
#             gameid, status, time_tag, data = result
#             if status == 200:
#                 if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
#                     break
#             all_data.append(data)
#         else:
#             return JSONResponse(
#                 content={"status": "success", "data": all_data},
#                 headers={"Cache-Control": "max-age=300, public"},
#             )
#         # sync
#         return JSONResponse(
#             content={
#                 "status": "success",
#                 "data": await _sync_curseforge_games(sess=session),
#             },
#             headers={"Cache-Control": "max-age=300, public"},
#         )

# @games_router.get(
#     "/curseforge/game/{gameid}",
#     responses={
#         200: {
#             "description": "Curseforge Game info",
#             "content": {
#                 "application/json": {
#                     "example": {"status": "success", "data": curseforge_game_example}
#                 }
#             },
#         }
#     },
#     description="Curseforge Game 信息",
#     tags=["Curseforge"],
# )
# async def curseforge_game(gameid: int):
#     return await _curseforge_get_game(gameid=gameid)
