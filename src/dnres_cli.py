import click
import contextlib
from datetime import datetime
from dnres import DnRes
import configparser
import os
import pandas as pd
from pyfzf.pyfzf import FzfPrompt
import subprocess
import sqlite3
import json
from flask import Flask, render_template, send_from_directory


@click.group(invoke_without_command=True)
@click.argument("config")
@click.pass_context
def dnres(ctx, config):
    """
    \b
    Prints the contents of the structure is no command is passed.
    """

    res = DnRes(config)
    ctx.obj = res

    if ctx.invoked_subcommand is None:
        print(res)


@dnres.command()
@click.option('--directory', '-d', required=True, help='Name of directory.')
@click.option('--filename', '-f', required=False, help='Filename in directory.')
@click.pass_obj
def info(res, directory, filename):
    """
    \b
    Shows information for directory or filename.
    Otherwise, it shows information for the passed filename of the passed directory.
    """

    if not filename:
        res.info_directory(directory)
    else:
        res.info_filename(directory, filename)


@dnres.command()
@click.option('--directory', '-d', required=True, help='Name of directory.')
@click.option('--filename', '-f', required=True, help='Filename in directory.')
@click.pass_obj
def delete(res, directory, filename):
    """
    \b
    Deletes stored object. 
    """

    res.delete(directory, filename)


@dnres.command()
@click.option('--filename', '-f', required=True, help='Filename to move.')
@click.option('--source', '-s', required=True, help='Directory in structure where data are stored.')
@click.option('--destination', '-d', required=True, help='Directory in structure where data will be moved to.')
@click.option('--overwrite', is_flag=True, help='Flag for overwriting previously stored data under same filename.')
@click.option('--db_only', is_flag=True, help='Flag for making changes only in database in case filename is reference to path.')
@click.pass_obj
def move(res, filename, source, destination, overwrite, db_only):
    """
    \b
    Moves stored objects from source to destination.
    If overwrite, stored objects with same name will be overwriten in destination.
    """

    if db_only:
        res.move(filename=filename,
                 source=source,
                 destination=destination,
                 overwrite=overwrite,
                 db_only=True)
    else:
        res.move(filename=filename,
                 source=source,
                 destination=destination,
                 overwrite=overwrite,
                 db_only=False)


@dnres.command()
@click.option('--directory', '-d', required=True, help='Directory where stored object is.')
@click.option('--previous', '-p', required=True, help='Previous filename of stored object.')
@click.option('--new', '-n', required=True, help='New filename of stored object.')
@click.pass_obj
def rename(res, directory, previous, new):
    """
    \b
    Renames stored object from previous filename to new filename.
    """

    res.rename(directory=directory,
               previous=previous,
               new=new)


@dnres.command()
@click.option('--description', '-i', required=True, help='Description to set for stored object.')
@click.option('--directory', '-d', required=True, help='Directory where stored object is.')
@click.option('--filename', '-f', required=True, help='Filename of the stored object.')
@click.pass_obj
def set_description(res, description, directory, filename):
    """
    \b
    Sets description for stored object.
    """

    res.set_description(description=description,
                        directory=directory,
                        filename=filename)


@dnres.command()
@click.option('--datatype', '-i', required=True, help='Datatype to set for stored object.')
@click.option('--directory', '-d', required=True, help='Directory where stored object is.')
@click.option('--filename', '-f', required=True, help='Filename of the stored object.')
@click.pass_obj
def set_datatype(res, datatype, directory, filename):
    """
    \b
    Sets datatype for stored object.
    """

    res.set_datatype(datatype=datatype,
                    directory=directory,
                    filename=filename)


@dnres.command()
@click.option('--source', '-s', required=True, help='Source information to set for stored object.')
@click.option('--directory', '-d', required=True, help='Directory where stored object is.')
@click.option('--filename', '-f', required=True, help='Filename of the stored object.')
@click.pass_obj
def set_source(res, source, directory, filename):
    """
    \b
    Sets source information for stored object.
    """

    res.set_source(source=source,
                   directory=directory,
                   filename=filename)


@dnres.command()
@click.option('--directory', '-d', required=True, help='Name of directory.')
@click.option('--filename', '-f', required=True, help='Filename in directory.')
@click.pass_obj
def ls(res, directory, filename):
    """
    \b
    Prints the filepath of the stored object or file.
    """

    filepath = os.path.join(res.structure[directory], filename)
    print(filepath)


@dnres.command()
@click.option('--data', required=True, help='Name of data to store.')
@click.option('--directory', '-d', required=True, help='Name of directory to store to.')
@click.option('--filename', '-f', required=True, help='Filename under which data will be stored.')
@click.option('--description', '-i', required=False, help='Brief description about the data.')
@click.option('--source', '-s', required=False, help='Where data came from.')
@click.option('--register', is_flag=True, help='Flag in case you only want to register file path to database.')
@click.option('--overwrite', is_flag=True, help='Flag for overwriting previously stored data under same filename.')
@click.pass_obj
def store(res, data, directory, filename, description, source, register, overwrite):
    """
    \b
    Stores data in structure and database.
    """
    
    res.store(data=data,
              directory=directory,
              filename=filename,
              source=source,
              description=description,
              register=register,
              isfile=True,
              overwrite=overwrite)


@dnres.command()
@click.option('--directory', '-d', required=True, help='Name of directory in db to store to.')
@click.option('--filename', '-f', required=True, help='How the registered directory will be referenced in the db.')
@click.option('--description', '-i', required=False, help='Brief description about the directory.')
@click.option('--source', '-s', required=False, help='Where directory came from.')
@click.pass_obj
def insert_dir_to_db(res, directory, filename, description, source):
    """
    \b
    Register whole directory that holds data to database.
    """

    date = int(datetime.today().strftime('%Y%m%d'))
    datatype = 'dir'
    res._insert_in_db(directory, 
                       date,
                       filename,
                       datatype,
                       description,
                       source)


@dnres.command()
@click.option('--directory', '-d', required=True, help='Name of directory.')
@click.option('--filename', '-f', required=True, help='Filename in directory.')
@click.option('--backend', '-b', required=True, type=click.Choice(['pandas', 'none']), 
              default='none', show_default=True, help="Backend to use in order to load and print objects or files.")
@click.option('--delimiter', required=False, type=click.Choice(['tab', 'comma']), help="Delimiter for csv or tsv files.")
@click.option('--sheet', type=int, required=False, help="Sheet number for excel files.")
@click.pass_obj
def cat(res, directory, filename, backend, delimiter, sheet):
    """
    \b
    It prints the contents of the stored object or file. 
    Prints filepath if stored data are not supported for printing.
    """

    # Identify object is serialized
    if filename.endswith(".json") or filename.endswith(".pickle"):
        serialization = True
    else:
        serialization = False
   
    if serialization:
        data = res.load(directory, filename)

        if isinstance(data, list) or isinstance(data, tuple) or isinstance(data, set):
            for item in data:
                print(item)

        elif isinstance(data, dict):
            print(json.dumps(data))

        elif isinstance(data, str):
            print(data)

        elif isinstance(data, pd.core.frame.DataFrame):
            print(data.to_csv(index=False, sep='\t'))

        else:
            print(os.path.join(res.structure[directory], filename))

    else:
        filepath = res.load(directory, filename)

        # Action for TXT files
        if filename.endswith('.txt'):
            if backend and backend != 'none':
                raise Exception('For txt file backend should be none.')
            with open(filepath, 'r') as inf:
                for line in inf:
                    line = line.strip("\n")
                    print(line)

        # Action for CSV or TSV files
        elif filename.endswith('.csv') or filename.endswith('.tsv'):
            if backend == 'none':
                with open(filepath, 'r') as inf:
                    for line in inf:
                        line = line.strip("\n")
                        if not delimiter or delimiter == 'tab':
                            line = line.split('\t')
                        elif delimiter == 'comma':
                            line = line.split(',')
                        print('\t'.join(line))
            elif backend == 'pandas':
                if not delimiter or delimiter == 'tab':
                    df = pd.read_csv(filepath, sep='\t')
                elif delimiter == 'comma':
                    df = pd.read_csv(filepath, sep=',')
                print(df.to_string())

        # Action for EXCEL files
        elif filename.endswith('.xls') or filename.endswith('.xlsx'):
            if backend == 'none':
                raise Exception("For excel files, backend cannot be none.")
            elif backend == 'pandas':
                if not sheet:
                    raise Exception("Sheet number should be passed for excel files.")
                df = pd.read_excel(filepath, sheet_name=sheet)
                print(df.to_string())

        else:
            print(filepath)



@dnres.command()
@click.option('--directory', '-d', required=True, help='Name of directory.')
@click.option('--filename', '-f', required=True, help='Filename in directory.')
@click.pass_obj
def view(res, directory, filename):
    """
    \b
    Use a user defined viewer to view the file.
    """

    # Identify object is serialized
    if filename.endswith(".json") or filename.endswith(".pickle"):
        serialization = True
    else:
        serialization = False
   
    if serialization:
        raise Exception("File is serialized. Use 'cat' command.")
    else:
        filepath = res.load(directory, filename)

        config = configparser.ConfigParser()
        config.read(res.config_file)
        if not config.has_section('VIEWER'):
            raise KeyError("With 'view' command, VIEWER section is required in the config file.")
        viewers = config['VIEWER'].keys()
        fzf = FzfPrompt()
        try:
            choice = fzf.prompt(viewers, '--exact')
        except Exception:
            exit("Action cancelled.")
        choice = choice[0]
        command = config['VIEWER'][choice]
        command = command.format(filepath)
        subprocess.run(command, shell=True)


@dnres.command()
@click.pass_obj
def webapp(res):
    """
    \b
    Starts a Flask server to view data and results."""
    app = Flask(__name__)

    @app.route('/')
    def index():
        data = dict()
        with contextlib.closing(sqlite3.connect(res.db)) as conn:
            with contextlib.closing(conn.cursor()) as c:
                for directory in res.structure.keys():
                    query = f"SELECT * FROM {directory}"
                    c.execute(query)
                    results = c.fetchall()
                    data[directory] = results
        return render_template('index.html', description=res.description, data=data)

    @app.route('/<directory>/<path:filename>')
    def serve_file(directory, filename):
        return send_from_directory(res.structure[directory], filename)

    app.run(debug=True, port=7000)


if __name__ == "__main__":
    dnres()
