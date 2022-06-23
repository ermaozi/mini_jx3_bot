from datetime import datetime
from enum import Enum

from nonebot import on_regex
from nonebot.adapters.onebot.v12.event import GroupMessageEvent
from nonebot.adapters.onebot.v12.message import MessageSegment
from nonebot.adapters.onebot.v12.permission import GROUP
from nonebot.consts import REGEX_DICT
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from src.params import PluginConfig
from src.utils.browser import browser
from src.utils.config import Config
from src.utils.log import logger

from . import data_source as source
from .config import DAILIY_LIST, JX3APP, JX3PROFESSION

__plugin_meta__ = PluginMetadata(
    name="剑三查询",
    description="剑三游戏查询，数据源使用jx3api",
    usage="参考“帮助”",
    config=PluginConfig()
)

all_config = Config()

# ----------------------------------------------------------------
#   正则枚举，已实现的查询功能
# ----------------------------------------------------------------


class REGEX(Enum):
    '''正则枚举'''
    日常任务 = r"(^日常$)|(^日常 [\u4e00-\u9fa5]+$)"
    开服检查 = r"(^开服$)|(^开服 [\u4e00-\u9fa5]+$)"
    金价比例 = r"(^金价$)|(^金价 [\u4e00-\u9fa5]+$)"
    沙盘图片 = r"(^沙盘$)|(^沙盘 [\u4e00-\u9fa5]+$)"
    推荐小药 = r"(^小药 [\u4e00-\u9fa5]+$)|(^[\u4e00-\u9fa5]+小药$)"
    推荐装备 = r"(^配装 [\u4e00-\u9fa5]+$)|(^[\u4e00-\u9fa5]+配装$)"
    推荐奇穴 = r"(^奇穴 [\u4e00-\u9fa5]+$)|(^[\u4e00-\u9fa5]+奇穴$)"
    查宏命令 = r"(^宏 [\u4e00-\u9fa5]+$)|(^[\u4e00-\u9fa5]+宏$)"
    阵眼效果 = r"(^阵眼 [\u4e00-\u9fa5]+$)|(^[\u4e00-\u9fa5]+阵眼$)"
    物品价格 = r"^物价 [\u4e00-\u9fa5]+$"
    随机骚话 = r"^骚话$"
    奇遇前置 = r"^((前置)|(条件)) [\u4e00-\u9fa5]+$"
    奇遇攻略 = r"(^攻略 [\u4e00-\u9fa5]+$)|(^[\u4e00-\u9fa5]+攻略$)"
    更新公告 = r"(^更新$)|(^公告$)|(^更新公告$)"
    奇遇查询 = r"(^查询 [(\u4e00-\u9fa5)|(@)]+$)|(^查询 [\u4e00-\u9fa5]+ [(\u4e00-\u9fa5)|(@)]+$)"
    奇遇统计 = r"(^奇遇 [\u4e00-\u9fa5]+$)|(^奇遇 [\u4e00-\u9fa5]+ [\u4e00-\u9fa5]+$)"
    奇遇汇总 = r"(^汇总$)|(^汇总 [\u4e00-\u9fa5]+$)"
    比赛战绩 = r"(^战绩 [(\u4e00-\u9fa5)|(@)]+$)|(^战绩 [\u4e00-\u9fa5]+ [(\u4e00-\u9fa5)|(@)]+$)"
    装备属性 = r"(^((装备)|(属性)) [(\u4e00-\u9fa5)|(@)]+$)|(^((装备)|(属性)) [\u4e00-\u9fa5]+ [(\u4e00-\u9fa5)|(@)]+$)"


# ----------------------------------------------------------------
#   matcher列表，定义查询的mathcer
# ----------------------------------------------------------------
daily_query = on_regex(pattern=REGEX.日常任务.value, permission=GROUP, priority=5, block=True)
server_query = on_regex(pattern=REGEX.开服检查.value, permission=GROUP, priority=5, block=True)
gold_query = on_regex(pattern=REGEX.金价比例.value, permission=GROUP, priority=5, block=True)
sand_query = on_regex(pattern=REGEX.沙盘图片.value, permission=GROUP, priority=5, block=True)
qixue_query = on_regex(pattern=REGEX.推荐奇穴.value, permission=GROUP, priority=5, block=True)
medicine_query = on_regex(pattern=REGEX.推荐小药.value, permission=GROUP, priority=5, block=True)
equip_group_query = on_regex(pattern=REGEX.推荐装备.value, permission=GROUP, priority=5, block=True)
macro_query = on_regex(pattern=REGEX.查宏命令.value, permission=GROUP, priority=5, block=True)
zhenyan_query = on_regex(pattern=REGEX.阵眼效果.value, permission=GROUP, priority=5, block=True)
condition_query = on_regex(pattern=REGEX.奇遇前置.value, permission=GROUP, priority=5, block=True)
strategy_query = on_regex(pattern=REGEX.奇遇攻略.value, permission=GROUP, priority=5, block=True)
update_query = on_regex(pattern=REGEX.更新公告.value, permission=GROUP, priority=5, block=True)
price_query = on_regex(pattern=REGEX.物品价格.value, permission=GROUP, priority=5, block=True)
serendipity_query = on_regex(pattern=REGEX.奇遇查询.value, permission=GROUP, priority=5, block=True)
serendipity_list_query = on_regex(pattern=REGEX.奇遇统计.value, permission=GROUP, priority=5, block=True)
serendipity_summary_query = on_regex(pattern=REGEX.奇遇汇总.value, permission=GROUP, priority=5, block=True)
saohua_query = on_regex(pattern=REGEX.随机骚话.value, permission=GROUP, priority=5, block=True)
match_query = on_regex(pattern=REGEX.比赛战绩.value, permission=GROUP, priority=5, block=True)
equip_query = on_regex(pattern=REGEX.装备属性.value, permission=GROUP, priority=5, block=True)
help = on_regex(pattern=r"^帮助$", permission=GROUP, priority=5, block=True)


# ----------------------------------------------------------------
#   Dependence，用来获取相关参数
# ----------------------------------------------------------------

async def get_server(matcher: Matcher, event: GroupMessageEvent, state: T_State) -> str:
    '''
    说明:
        Dependence，获取匹配字符串中的server，如果没有则获取群绑定的默认server
    '''
    regex_dict: dict = state[REGEX_DICT]
    _server = regex_dict.get("server")
    if _server:
        server = await source.get_main_server(_server)
        if not server:
            msg = f"未找到服务器[{_server}]，请验证后查询。"
            await matcher.finish(msg)
    else:
        server = await source.get_server(event.group_id)
    return server


async def get_value(state: T_State) -> str:
    '''
    说明:
        Dependence，获取匹配字符串中的value字段
    '''
    regex_dict: dict = state[REGEX_DICT]
    return regex_dict['value']


async def get_profession(matcher: Matcher, name: str = Depends(get_value)) -> str:
    '''获取职业名称'''
    profession = JX3PROFESSION.get_profession(name)
    if profession:
        return profession

    # 未找到职业
    msg = f"未找到职业[{name}]，请检查参数。"
    await matcher.finish(msg)


# ----------------------------------------------------------------
#   handler列表，具体实现回复内容
# ----------------------------------------------------------------


@daily_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server)):
    '''日常查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 日常查询 | 请求：{server}"
    )
    params = {
        "server": server,
        "next": 0
    }
    msg, data = await source.get_data_from_api(app=JX3APP.日常任务, group_id=event.group_id, params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await daily_query.finish(msg)

    msg = f'日常[{server}]\n'
    msg += f'当前时间：{data.get("date")} 星期{data.get("week")}\n'
    msg += f'今日大战：{data.get("war")}\n'
    msg += f'今日战场：{data.get("battle")}\n'
    msg += f'公共任务：{data.get("public")}\n'
    msg += f'阵营任务：{data.get("camp")}\n'
    msg += DAILIY_LIST.get(data.get("week"))
    if data.get("draw") is not None:
        msg += f'美人画像：{data.get("draw")}\n'
    team: list = data.get("team")
    msg += f'\n武林通鉴·公共任务\n{team[0]}\n'
    msg += f'武林通鉴·秘境任务\n{team[1]}\n'
    msg += f'武林通鉴·团队秘境\n{team[2]}'
    await daily_query.finish(msg)


@server_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server)):
    '''开服查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 开服查询 | 请求：{server}"
    )
    params = {
        "server": server
    }
    msg, data = await source.get_data_from_api(app=JX3APP.开服检查, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await server_query.finish(msg)

    status = "已开服" if data['status'] == 1 else "维护中"
    msg = f'{data.get("server")} 当前状态是[{status}]'
    await server_query.finish(msg)


@gold_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server)):
    '''金价查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 金价查询 | 请求：{server}"
    )
    params = {
        "server": server
    }
    msg, data = await source.get_data_from_api(app=JX3APP.金价比例, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await gold_query.finish(msg)

    data = data[0]
    date_now = datetime.now().strftime("%m-%d %H:%M")
    msg = f'金价[{data.get("server")}] {date_now}\n'
    msg += f'官方平台：1元={data.get("wanbaolou")}金\n'
    msg += f'百度贴吧：1元={data.get("tieba")}金\n'
    msg += f'悠悠平台：1元={data.get("uu898")}金\n'
    msg += f'嘟嘟平台：1元={data.get("dd373")}金\n'
    msg += f'其他平台：1元={data.get("5173")}金'
    await gold_query.finish(msg)


@sand_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server)):
    '''沙盘查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 沙盘查询 | 请求：{server}"
    )
    params = {
        "server": server
    }
    msg, data = await source.get_data_from_api(app=JX3APP.沙盘图片, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await sand_query.finish(msg)

    url = data[0]['url']
    time: int = data[0]['time']
    day = datetime.fromtimestamp(time).strftime("%m-%d %H:%M")
    msg = f"【{server}】沙盘，更新时间：{day}"+MessageSegment.image(url)
    await sand_query.finish(msg)


@qixue_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_profession)):
    '''奇穴查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 奇穴查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.推荐奇穴, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await qixue_query.finish(msg)

    msg = f'【{data.get("name")}】奇穴推荐，时间：{data.get("time")}\n'
    msg += "龙门绝境：\n"+MessageSegment.image(data.get("longmen"))
    msg += "战场任务：\n"+MessageSegment.image(data.get("battle"))
    await qixue_query.finish(msg)


@medicine_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_profession)):
    '''小药查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 小药查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.推荐小药, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await medicine_query.finish(msg)

    name = data.get('name')
    msg = f'[{name}]小药：\n'
    msg += f'增强食品：{data.get("heighten_food")}\n'
    msg += f'辅助食品：{data.get("auxiliary_food")}\n'
    msg += f'增强药品：{data.get("heighten_drug")}\n'
    msg += f'辅助药品：{data.get("auxiliary_drug")}'

    await medicine_query.finish(msg)


@equip_group_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_profession)):
    '''配装查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 配装查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.推荐装备, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await equip_group_query.finish(msg)

    msg = MessageSegment.text(f'{data.get("name")}配装：\nPve装备：\n')+MessageSegment.image(data.get("pve")) + \
        MessageSegment.text("Pvp装备：\n")+MessageSegment.image(data.get("pvp"))
    await equip_group_query.finish(msg)


@macro_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_profession)):
    '''宏查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 宏查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.查宏命令, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await macro_query.finish(msg)

    msg = f'宏 {data.get("name")} 更新时间：{data.get("time")}\n'
    msg += f'{data.get("macro")}\n'
    msg += f'奇穴：{data.get("qixue")}'

    await macro_query.finish(msg)


@zhenyan_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_profession)):
    '''阵眼查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 阵眼查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.阵眼效果, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await zhenyan_query.finish(msg)

    msg = f"{name}：【{data.get('skillName')}】\n"
    descs: list[dict] = data.get("descs")
    for i in descs:
        msg += f"{i.get('name')}：{i.get('desc')}\n"
    await zhenyan_query.finish(msg)


@condition_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_value)):
    '''前置查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 前置查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.奇遇前置, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await condition_query.finish(msg)

    url = data.get("upload")
    msg = MessageSegment.image(url)
    await condition_query.finish(msg)


@strategy_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_value)):
    '''攻略查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 攻略查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    # 判断有没有token
    token = all_config.jx3api['jx3_token']
    if token is None:
        msg, data = await source.get_data_from_api(app=JX3APP.免费奇遇攻略, group_id=event.group_id,  params=params)
    else:
        msg, data = await source.get_data_from_api(app=JX3APP.付费奇遇攻略, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await strategy_query.finish(msg)

    img = data['url']
    await strategy_query.finish(MessageSegment.image(img))


@update_query.handle()
async def _(event: GroupMessageEvent):
    '''更新公告'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 更新公告查询"
    )
    url = "https://jx3.xoyo.com/launcher/update/latest.html"
    img = await browser.get_image_from_url(url=url, width=130)
    msg = MessageSegment.image(img)
    log = f"群{event.group_id} | 查询更新公告"
    logger.info(log)
    await update_query.finish(msg)


@saohua_query.handle()
async def _(event: GroupMessageEvent):
    '''骚话'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 骚话 | 请求骚话"
    )
    msg, data = await source.get_data_from_api(app=JX3APP.随机骚话, group_id=event.group_id, params=None)
    if msg != "success":
        msg = f"请求失败，{msg}"
        await saohua_query.finish(msg)

    await saohua_query.finish(data['text'])

# -------------------------------------------------------------
#   下面是使用模板生成的图片事件
# -------------------------------------------------------------


@price_query.handle()
async def _(event: GroupMessageEvent, name: str = Depends(get_value)):
    '''物价查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 物价查询 | 请求：{name}"
    )
    params = {
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.物品价格, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await price_query.finish(msg)

    pagename = "price.html"
    item_name = data.get("name")
    item_info = data.get("info")
    item_img = data.get("upload")
    item_data = source.handle_data_price(data.get("data"))
    img = await browser.template_to_image(pagename=pagename,
                                          name=item_name,
                                          info=item_info,
                                          image=item_img,
                                          data=item_data
                                          )
    await price_query.finish(MessageSegment.image(img))


@serendipity_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server), name: str = Depends(get_value)):
    '''角色奇遇查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 角色奇遇查询 | 请求：server:{server},name:{name}"
    )
    params = {
        "server": server,
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.奇遇查询, group_id=event.group_id,  params=params, need_ticket=True)

    if msg != "success":
        msg = f"查询失败，{msg}"
        await serendipity_query.finish(msg)

    pagename = "serendipity.html"
    get_data = source.handle_data_serendipity(data)
    img = await browser.template_to_image(pagename=pagename,
                                          server=server,
                                          name=name,
                                          data=get_data
                                          )
    await serendipity_query.finish(MessageSegment.image(img))


@serendipity_list_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server), name: str = Depends(get_value)):
    '''奇遇统计查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 奇遇统计查询 | 请求：server:{server},serendipity:{name}"
    )
    params = {
        "server": server,
        "serendipity": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.奇遇统计, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await serendipity_list_query.finish(msg)

    pagename = "serendipity_list.html"
    get_data = source.handle_data_serendipity_list(data)
    img = await browser.template_to_image(pagename=pagename,
                                          server=server,
                                          name=name,
                                          data=get_data
                                          )
    await serendipity_list_query.finish(MessageSegment.image(img))


@serendipity_summary_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server)):
    '''奇遇汇总查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 奇遇汇总查询 | 请求：{server}"
    )
    params = {
        "server": server
    }
    msg, data = await source.get_data_from_api(app=JX3APP.奇遇汇总, group_id=event.group_id,  params=params)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await serendipity_summary_query.finish(msg)

    pagename = "serendipity_summary.html"
    get_data = source.handle_data_serendipity_summary(data)
    img = await browser.template_to_image(pagename=pagename,
                                          server=server,
                                          data=get_data
                                          )
    await serendipity_summary_query.finish(MessageSegment.image(img))


@match_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server), name: str = Depends(get_value)):
    '''战绩查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 战绩查询 | 请求：server:{server},name:{name}"
    )
    params = {
        "server": server,
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.比赛战绩, group_id=event.group_id,  params=params, need_ticket=True)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await match_query.finish(msg)

    pagename = "match.html"
    get_data = source.handle_data_match(data)
    img = await browser.template_to_image(pagename=pagename,
                                          server=server,
                                          name=name,
                                          data=get_data
                                          )
    await match_query.finish(MessageSegment.image(img))


@equip_query.handle()
async def _(event: GroupMessageEvent, server: str = Depends(get_server), name: str = Depends(get_value)):
    '''装备属性查询'''
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 装备属性查询 | 请求：server:{server},name:{name}"
    )
    params = {
        "server": server,
        "name": name
    }
    msg, data = await source.get_data_from_api(app=JX3APP.装备属性, group_id=event.group_id,  params=params, need_ticket=True)
    if msg != "success":
        msg = f"查询失败，{msg}"
        await equip_query.finish(msg)

    pagename = "equip.html"
    get_data = source.handle_data_equip(data)
    img = await browser.template_to_image(pagename=pagename,
                                          server=server,
                                          name=name,
                                          data=get_data
                                          )
    await equip_query.finish(MessageSegment.image(img))


@help.handle()
async def _(event: GroupMessageEvent):
    '''帮助'''
    token = all_config.jx3api['jx3_token']
    flag = token is not None
    pagename = "search_help.html"
    img = await browser.template_to_image(pagename=pagename, flag=flag)
    await help.finish(MessageSegment.image(img))
