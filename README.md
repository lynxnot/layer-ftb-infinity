# Overview

This charm deploys an instance of Minecraft Feed The Beast - Infinity Evolved Skyblock

FTB Infinity Evolved Skyblock is a modpack designed to provide an extra challenge
for any experienced Minecrafter. Work your way through new recipes, twisted game mechanics,
and collect the rare and mysterious trophies! Warning, may consume a vast amount of your time.

This pack contains Fastcraft, by Player. Fastcraft enhances Minecraft with increased
performance. Bug reports being made directly to Mod Authors should state Fastcraft is enabled.

# Usage

By deploying this charm the user accept the [Minecraft EULA](https://account.mojang.com/documents/minecraft_eula).

Step by step instructions on using the charm:

    juju deploy ftb-infinity
    juju deploy --series xenial openjdk
    juju add-relation ftb-infinity openjdk

The server will be available on the configured port, 25565 by default.

You need to OP yourself to create an island, the server console is accessible on a screen session:

    juju ssh <machine-id>
    sudo -u ftb-run -i
    # switch pts device to allow screen usage
    script /dev/null
    screen -r -S ftb-infinity
    op your_minecraft_username

To get out of screen use the default key combination (CTRL-a)+(d)

To play you need the [FTB launcher](http://www.feed-the-beast.com/).


## Scale out Usage

This charm do not support scaling.

## Known Limitations and Issues

The update-status hook is not implemented at the moment.

Updating the modpack is unsupported.

If the configuration is modified after having changed server options via the game console,
the initial values will be restored.

# Configuration

This charm deploys a standard server configuration with difficulty set to normal.

The configuration supports changing the max amount of RAM and the TCP port.

# Contact Information

This charm is hosted on [github](https://github.com/lynxnot/layer-ftb-infinity)

## Upstream Project Name

- [FTB - Infinity Evolved](http://www.feed-the-beast.com/projects/ftb-infinity-evolved-skyblock)
- [FTB launcher](http://www.feed-the-beast.com/)
- [Minecraft](https://minecraft.net)
- [Minecraft EULA](https://account.mojang.com/documents/minecraft_eula)
