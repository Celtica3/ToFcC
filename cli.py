import os
import click
from click_shell import shell
from TofCube.manager import CubeManager
import logging
import sys
#get real path of the executed program
PROGRAM_LOCATION = os.path.dirname(os.path.realpath(sys.argv[0]))

# run first
@shell(invoke_without_command=True)
@click.option('-d','--debug', is_flag=True)
@click.pass_context
def cli(ctx, debug):
    if debug:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    manager: CubeManager = CubeManager.create(PROGRAM_LOCATION)
        
    # pass into ctx
    ctx.obj : CubeManager = manager
    
    if ctx.invoked_subcommand is None:
        # run help
        click.echo(ctx.get_help())

@cli.command("swap", help="swap a profile")
@click.argument("name")
@click.option("-p", "--password", default=None)
# kill flag and relaunch flag
@click.option("-nk","--nokill", is_flag=True)
@click.option("-r","--relaunch", is_flag=True)
@click.pass_context
def _swap(ctx, name : str, password :str, nokill, relaunch):
    manager : CubeManager = ctx.obj
    try:
        manager.swap(
            name,
            password=password,
            kill=not nokill,
            relaunch=relaunch
        )
    except Exception as e:
        logging.error(e)
        click.echo("an error occurred")
        raise
    
    click.echo("swap successful")


@cli.command("bkup", help="backup current logged in user")
@click.argument("name")
# alias allow multiple
@click.option("-a","--alias", multiple=True)
@click.option("-p","--password", default=None)
@click.option("-re","--removeOnExist", is_flag=True)
@click.pass_context
def _backup(ctx, name  : str, alias, password, removeonexist):
    manager : CubeManager = ctx.obj
    try:
        manager.backup(
            name,
            *alias,
            customPassword=password,
            conflictOnTargetExist="remove" if removeonexist else "rename"
        )
    except Exception as e:
        logging.error(e)
        click.echo("an error occurred")
        raise
    
    click.echo("backup successful")

@cli.command("exit")
@click.pass_context
def _exit(ctx):
    os.abort()

@cli.command("spoof",help="get tof launcher directory by spoofing processes")
@click.pass_context
def spoof(ctx):
    manager : CubeManager = ctx.obj
    manager.tofLauncherLocation = CubeManager.findLauncher()
    print(manager.tofLauncherLocation )
    if manager.tofLauncherLocation:
        manager.saveConfig(manager.configDir, **manager.dict(exclude_defaults=True))
    
@cli.command("lau", help="launch launcher")
@click.option("-f", "--folder", is_flag = True)
@click.pass_context
def _open_launcher(ctx, folder):
    manager : CubeManager = ctx.obj
    if folder:
        return os.startfile(manager.tofLauncherLocation)
    manager.openLauncher()

@cli.command("roam", help="open the tof_launcher folder in roaming")
@click.pass_context
def _open_roaming_folder(ctx):
    manager : CubeManager = ctx.obj
    folder = manager.tofRoamingLocation
    if folder:
        os.startfile(folder)
        
@cli.command("configDir", help="open config folder")
@click.pass_context
def _open_configDir(ctx):
    manager : CubeManager = ctx.obj
    folder = manager.configDir
    os.startfile(folder)
    
@cli.command("verify", help="verify listing")
@click.pass_context
def _verify(ctx):
    manager : CubeManager = ctx.obj
    manager.verify()

@cli.command("list")
@click.pass_context
def _list_profiles(ctx):
    manager : CubeManager = ctx.obj
    for p in manager.profiles:
        print(f"{p.name}", end="")
        if p.alias:
            print({','.join(p.alias)})
        else:
            print()

if __name__ == "__main__":
    cli()
