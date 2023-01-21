import json
import os
import click
from click_shell import shell
from ToFcC.base import *
import logging
import sys
#get real path of the executed program
PROGRAM_LOCATION = os.path.dirname(os.path.realpath(sys.argv[0]))

CUBFIG_FOLDER =os.path.join(PROGRAM_LOCATION, "ToFCubfig")

CUBFIG_PATH = os.path.join(CUBFIG_FOLDER,"config.json")

# run first
@shell(invoke_without_command=True)
@click.option('--debug', is_flag=True)
@click.option('--clear', is_flag=True)
@click.pass_context
def cli(ctx, debug, clear):
    if debug:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    if clear and os.path.exists(CUBFIG_PATH):
        # remove json file
        os.remove(CUBFIG_PATH)
        
    # ensure folder
    os.makedirs(CUBFIG_FOLDER, exist_ok=True)
    logging.info("creating folder at %s", CUBFIG_FOLDER)
    # ensure config
    if not os.path.exists(CUBFIG_PATH):
        logging.info("creating config at %s", CUBFIG_PATH)
        with open(CUBFIG_PATH, "w") as f:
            f.write("{}")
    
    # load config
    try:
        with open(CUBFIG_PATH, "r") as f:
            raw = json.load(f)
    except:
        click.echo("config corrupted")
        os.abort()
        
    config = TConfig(**raw, dir=PROGRAM_LOCATION)
        
    # pass into ctx
    ctx.obj = config
    
    if ctx.invoked_subcommand is None:
        # run help
        click.echo(ctx.get_help())
        

@cli.command("swap")
@click.argument("name")
@click.pass_context
def _swap(ctx, name : str):
    try:
        ctx.obj.swap(name)
    except Exception as e:
        logging.error(e)
        click.echo("an error occurred")
        raise
    
    click.echo("swap successful")

@cli.command("backup")
@click.argument("name")
@click.option('--force', is_flag=True)
@click.pass_context
def _backup(ctx, name  : str, force):
    try:
        ctx.obj.backup(name, not force)
    except Exception as e:
        logging.error(e)
        click.echo("an error occurred")
        raise
    
    click.echo("backup successful")

@cli.command("exit")
@click.pass_context
def _exit(ctx):
    os.abort()

@cli.command("spoof")
@click.pass_context
def spoof(ctx):
    print(ctx.obj.applicationLocation)
    ctx.obj.save()
    
@cli.command("open")
@click.argument("name")
@click.pass_context
def _open(ctx, name):
    # pass
    if name == "launcher" and ctx.obj.applicationLocation is not None:
        #start launcher
        address = os.path.join(ctx.obj.applicationLocation, "tof_launcher.exe")
        logging.info("starting: " +address)
        os.startfile(address)
        os.abort()
        
    elif name in ["appdata","roam","roaming"]:
        # open folder
        os.startfile(ctx.obj.roamingLocation)
    else:
        print("invalid")

if __name__ == "__main__":
    cli()
