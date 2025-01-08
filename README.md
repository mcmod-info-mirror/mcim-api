# MCmod-info-mirror

![mcim](https://socialify.git.ci/mcmod-info-mirror/mcim/image?description=1&font=Inter&issues=1&language=1&name=1&owner=1&pattern=Overlapping%20Hexagons&pulls=1&stargazers=1&theme=Auto)

为各平台的 Mod 的缓存加速，由 [MCLF-CN #3](https://github.com/MCLF-CN/docs/issues/3) 提议，由[鸣谢列表](#鸣谢)内的各位提供支持~

基于 [BMCLAPI](https://bmclapidoc.bangbang93.com) 使用网盘缓存的先例，当前文件缓存在试运行...

**急需节点加入 orz ！详情见 [OpenMCIM 文件分发相关 #91](https://github.com/mcmod-info-mirror/mcim/issues/91)**

以 [Curseforge](https://curseforge.com/) 和 [Modrinth](https://modrinth.com/) 为镜像源

- [API](https://mod.mcimirror.top)
- [Docs](https://mod.mcimirror.top/docs)
- 同步日志见 Telegram 频道：https://t.me/mcim_sync

## 接入

本镜像可能会添加 UA 白名单，请在使用前提交启动器的 UA [启动器信息](https://github.com/mcmod-info-mirror/mcim/issues/4)

## 使用

以下所有内容均建立在熟悉官方 API 的基础上，不了解的话请前往 [CFCore](https://docs.curseforge.com) 和 [Modrinth Docs](https://docs.modrinth.com) 参考。

MCIM 100% 兼容官方的 API 结构，可以直接替换，方便迁移，可以直接替换，具体可以比对 [Docs](https://mod.mcimirror.top/docs)，你可以在里面尝试。

### Modrinth

- `api.modrinth.com` or `staging-api.modrinth.com` -> `mod.mcimirror.top/modrinth`
- `cdn.modrinth.com` -> `mod.mcimirror.top`

### Curseforge

- `api.curseforge.com` -> `mod.mcimirror.top/curseforge`
- `edge.forgecdn.net` or `mediafilez.forgecdn.net` -> `mod.mcimirror.top`

### 简介翻译

[translate-mod-summary](https://github.com/mcmod-info-mirror/translate-mod-summary) 提供已缓存的 Mod 的简介的 GPT 翻译，定期更新

- Modrinth `description` -> `translated_description`
- Curseforge `summary` -> `translated_summary`

示例

<details>
  <summary>Modrinth</summary>
  <pre><blockcode> 
  {
    id: 'AANobbMI',
    description: 'The fastest and most compatible rendering optimization mod for Minecraft',
    ...
    found: true,
    slug: 'sodium',
    sync_at: '2024-07-22T08:30:37Z',
    translated_description: '一个为《我的世界》打造的现代渲染引擎，极大地提升了性能。'
  }
    
  </blockcode></pre>
</details>

<details>
  <summary>Curseforge</summary>
  <pre><blockcode> 
  {
    id: 975558,
    slug: 'progetto-multiverso-ultra-adventure',
    ...
    summary: 'This mod adds many new RPG features to the game',
    sync_at: '2024-06-06T01:23:21Z',
    translated_summary: '此模组为游戏添加了许多新的角色扮演特性。'
  }
  </blockcode></pre>
</details>

## 缓存思路

定时更新已缓存 Mod 信息，详见 [mcim-sync](https://github.com/mcmod-info-mirror/mcim-sync)**

已缓存 **绝大多数** 符合条件的 Modrinth 和 Curseforge 上的 Mod。

由于除了搜索接口是反代，其他都是通过数据库缓存，无法保证一定所需数据已缓存，也可能过期。

基本思路为 **忽视数据是否过期**，以及 **忽略数据是否不全**，无条件返回已有数据，在部分 Mod 未找到等情况下先返回数据，然后后台拉取源站。

不可信的响应将在 `headers` 内提供 `Trustable` 参数，提供 `sync_at` 缓存时间

关于文件缓存，不会缓存**除 Mod 外**的整合包、资源包、材质包、地图等，以及文件大小大于 **20M** 的文件，Curseforge 的类型限制为 `classId=6`，该限制会被可能根据需求更改。

## 注意事项

**文件**下载可能存在一定的不稳定性，当前缺少多节点网盘的分流，建议启动器在未能成功下载的情况下才尝试使用镜像源。

未缓存部分接口，如果有 API 需要更新或新增请联系。

关于 Mod 开发者收益问题，由于 API 下载量并不计入收益，因此无论从启动器官方源下载还是镜像源下载都是无法为 Mod 开发者提供收益的，不接受影响 Mod 开发者收益的指责。详情见 [MCLF-CN #3](https://github.com/MCLF-CN/docs/issues/3) 的讨论。

本镜像可能会在滥用的情况下切换到 Cloudflare CDN 或开启 URL 鉴权，或者暂时关闭。

缓存统计信息见 https://mod.mcimirror.top/statistics

2024/11/03 当前已缓存
```json
{
    "curseforge": {
        "mod": 75608,
        "file": 1265295,
        "fingerprint": 1264242
    },
    "modrinth": {
        "project": 42832,
        "version": 415463,
        "file": 458875
    },
    "file_cdn": {
        "file": 924555
    }
}
```

## 部署

先安装 docker，clone 到本地后直接 `docker-compose up -d` 即可，记得修改 `docker-compose.yml` 里面的 `config` 挂载目录，以及 `config` 内容。

## OpenMCIM

和 [OpenBMCLAPI](https://github.com/bangbang93/openbmclapi) 需要节点分发文件，欢迎~~急需~~节点加入，见 [OpenMCIM 文件分发相关 #91](https://github.com/mcmod-info-mirror/mcim/issues/91)

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

4. **禁止二次封装协议**  
   禁止在 MCIM 上对接口进行二次封装。

如有违反上述内容，MCIM 保留采取必要措施或终止服务的权利。

NOT AN OFFICIAL MINECRAFT SERVICE. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT. 不是 Minecraft 官方服务。未经 Mojang 或 MICROSOFT 批准或与 MOJANG 或 MICROSOFT 相关。
