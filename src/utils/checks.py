from discord.ext import commands


def is_server_owner():
    async def predicate(ctx: commands.Context):
        return ctx.author.id == ctx.guild.owner_id

    return commands.check(predicate)


def check_perms(perm_name: str):
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True

        fp_cog = ctx.bot.get_cog("FakePerms")
        if not fp_cog:
            raise commands.CheckFailure("FakePerms Cog not activated")

        role_ids = [role.id for role in ctx.author.roles]

        for role_id in role_ids:
            role_perms = fp_cog.get_role_permissions(role_id)
            admin_flag = fp_cog.permission_flags.get("ADMINISTRATOR")
            perm_flag = fp_cog.permission_flags.get(perm_name.upper())
            if perm_flag and (role_perms & perm_flag):
                return True
            elif admin_flag and (role_perms & admin_flag):
                return True

        raise commands.MissingPermissions([perm_name])

    return commands.check(predicate)
