# mcim-api

![mcim-api](https://socialify.git.ci/mcmod-info-mirror/mcim-api/image?description=1&font=Inter&issues=1&language=1&name=1&owner=1&pattern=Overlapping%20Hexagons&pulls=1&stargazers=1&theme=Auto)

为各平台的 Mod 的 API 缓存加速，由 [MCLF-CN #3](https://github.com/MCLF-CN/docs/issues/3) 提议，由[鸣谢列表](#鸣谢)内的各位提供支持~

已缓存 **绝大多数** 的 Modrinth 和 Curseforge 上的 Minecraft Mod 信息。缓存统计信息见 [mcim-statistics](https://mod.mcimirror.top/statistics)。

> [!WARNING]
> 由于多种原因，OpenMCIM 已暂停运行，MCIM API 不受影响。文件下载已自动重定向会源站。
> 高考完后可能后可能重制后投入使用，敬请期待。

效仿 [BMCLAPI](https://bmclapidoc.bangbang93.com) ，当前 OpenMCIM 文件缓存在试运行。**急需节点加入 orz ！详情见 [OpenMCIM 文件分发相关 #91](https://github.com/mcmod-info-mirror/mcim/issues/91)**。

API 支持 [Curseforge](https://curseforge.com/) 和 [Modrinth](https://modrinth.com/)。

- [API](https://mod.mcimirror.top)
- [Docs](https://mod.mcimirror.top/docs)
- [MCIM 同步进度](https://t.me/mcim_sync)
- [Status](https://status.mcimirror.top)

## 接入

本镜像可能会添加 UA 白名单，请在使用前提交启动器的 UA [启动器信息](https://github.com/mcmod-info-mirror/mcim/issues/4)。

## 使用

不了解官方 API 的话请前往 [CFCore](https://docs.curseforge.com) 和 [Modrinth Docs](https://docs.modrinth.com) 参考。

MCIM 几乎完美兼容官方的 API 结构，可以直接替换 URL，方便迁移，具体可以比对 [Docs](https://mod.mcimirror.top/docs)，你可以在里面尝试。

部分接口已忽略未实现，如果官方 API 有更新或新增，未及时跟进，请联系。

### Modrinth

- `api.modrinth.com` -> `mod.mcimirror.top/modrinth`
- `cdn.modrinth.com` -> `mod.mcimirror.top`

### Curseforge

- `api.curseforge.com` -> `mod.mcimirror.top/curseforge`
- `edge.forgecdn.net` or `mediafilez.forgecdn.net` -> `mod.mcimirror.top`

## 缓存相关

关于缓存，详见 [mcim-sync](https://github.com/mcmod-info-mirror/mcim-sync)

**MCIM 有可能随着风控策略的改变，无法及时更新缓存数据。如果有需要，启动器应该自行检查缓存日期并决定是否信任响应。**

每一个来自 MCIM 缓存的 API 响应，都会提供该响应对应的缓存日期，位于 Headers 的 `sync_at` 字段，格式为 `YYYY-MM-DDTHH:MM:SSZ`。同一个响应中，可能包含多个 `sync_at` 字段对应响应的不同部分。

### 简介翻译

简介原文来自 Modrinth Project 的 `description` 和 Curseforge Mod 的 `summary` 字段

详情见 [translate-mod-summary](https://github.com/mcmod-info-mirror/translate-mod-summary)，API 详情见[接口文档](https://mod.mcimirror.top/docs#/translate)

#### Modrinth

POST `https://mod.mcimirror.top/translate/modrinth`

URL 参数：`project_id`

例如 <https://mod.mcimirror.top/translate/modrinth?project_id=P7dR8mSH>

```json
{
  "project_id": "P7dR8mSH",
  "translated": "轻量级且模块化的API，为使用Fabric工具链的模组提供了常见的钩子功能和互操作性措施。",
  "original": "Lightweight and modular API providing common hooks and intercompatibility measures utilized by mods using the Fabric toolchain.",
  "translated_at": "2025-02-02T08:53:28.638000"
}
```

#### Curseforge

POST `https://mod.mcimirror.top/translate/curseforge`

URL 参数：`modId`

例如 <https://mod.mcimirror.top/translate/curseforge?modId=238222>

```json
{
  "modId": 238222,
  "translated": "查看物品和配方",
  "original": "View Items and Recipes",
  "translated_at": "2025-02-02T10:01:52.805000"
}
```

## OpenMCIM

> [!WARNING]
> 由于多种原因，OpenMCIM 已暂停运行，MCIM API 不受影响。文件下载已自动重定向会源站。
> 高考完后可能后可能重制后投入使用，敬请期待。

和 [OpenBMCLAPI](https://github.com/bangbang93/openbmclapi) 需要节点分发文件，**急需节点加入 orz ！** 见 [OpenMCIM 文件分发相关 #91](https://github.com/mcmod-info-mirror/mcim/issues/91)

对于启动器开发者，OpenMCIM 不会缓存**除 Mod 外**的整合包、资源包、材质包、地图等，以及文件大小大于 **20MB** 的文件，Curseforge 的类型限制为 `classId=6`，该限制会被可能根据需求更改。

## 注意事项

**文件**下载可能存在一定的不稳定性，当前缺少多节点网盘的分流，建议启动器在未能成功下载的情况下才尝试使用镜像源。

该 API 只提供 Minecraft 相关内容，不支持 Curseforge 上的其他游戏例如 wow。

关于 Mod 开发者收益问题，由于 API 下载量并不计入收益，因此无论从启动器官方源下载还是镜像源下载都是无法为 Mod 开发者提供收益的，不接受影响 Mod 开发者收益的指责。

**本镜像可能会在滥用或遭到攻击的情况下暂时关闭。**

**这是一项公益服务，请不要攻击我们**

## 鸣谢

- [Pysio](https://github.com/pysio2007) 提供 CDN 和域名
- [BangBang93](https://blog.bangbang93.com/) 提供服务器
- [SaltWood_233](https://github.com/SALTWOOD) 提供文件分发主控技术支持
- [为 OpenMCIM 提供节点支持的各位](https://files.mcimirror.top/dashboard/rank)

## 联系

- Email: z0z0r4@outlook.com
- QQ: 3531890582
- QQ 群聊 [OpenMCIM](https://qm.qq.com/q/ZSN6ilHEwC)

### 声明

MCIM 是一个镜像服务平台，旨在为中国大陆用户提供稳定的 Mod 信息镜像服务。为维护 Mod 创作者及源站平台的合法权益，MCIM 制定以下协议及处理方式：

1. **文件归属**  
   MCIM 平台镜像的所有文件，除 MCIM 本身的相关配置外，其所有权依据源站平台的协议进行归属。未经原始版权所有者授权，严禁通过 MCIM 进行任何形式的转发或二次发布。

2. **责任免责**  
   MCIM 将尽力确保所镜像信息的完整性、有效性和实时性。然而，对于通过 MCIM 使用的引发的任何纠纷或责任，MCIM 不承担任何法律责任，所有风险由用户自行承担。

3. **禁止二次封装协议**  
   禁止在 MCIM 上对接口进行二次封装。

如有违反上述内容，MCIM 保留采取必要措施或终止服务的权利。

NOT AN OFFICIAL MINECRAFT SERVICE. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.

不是 Minecraft 官方服务。未经 Mojang 或 MICROSOFT 批准或与 MOJANG 或 MICROSOFT 相关。
