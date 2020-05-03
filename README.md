# Gear Store Inventory

A [flask](https://flask.palletsprojects.com/) web application to manage an inventory of physical items, with data stored in a json file. associated image/binary files are stored separately.

This software was developed as a proof-of-concept to be used to manage [MUMC's](https://www.mumc.org.au/) ski gear inventory, and was used to do so for 1 year. It is currently in the process of being adapted to be more generic and capable of being used to manage any other similar kind of inventory.

Features:

- Easy to set up and host yourself, or use locally.
- Single human-readable file format.
- CSV file export.
- User defined categories.

## Screenshots

## Planned Upgrades

### Update 1

- [x] download inventory json button
- [x] download inventory csv button
- [ ] download inventory zip button (including images)
- [ ] serve from photo directory specified in json
- [ ] multiple inventories at once
- [ ] delete and upload image options in edit item page
- [x] upload images
- [ ] view backups
- [ ] support schema versioning and migrations

### Update 2

- [ ] resize image on upload
- [ ] create setup.py and have this be installed and run as a local command
- [x] command line options
- [ ] release to github
- [ ] new inventory page/dialog

## Running

### Dependencies

- Requires Python 3.
- See [requirements.txt](requirements.txt). These can be installed with `pip install -r requirements.txt` command.

### Command Line Arguments

```man
Gear Store Inventory

Usage:
  main.py [-p <port>] [-a <address>] new
  main.py [-p <port>] [-a <address>] <file>
  main.py (-h | --help)

Arguments:
  <file>        a json file containing an existing inventory
  <address>     an ip address of an interface on your computer
  <port>        an available port number on your computer

Options:
  -p <port>     port to host webserver on [default: 8090]
  -a <address>  address to host webserver on [default: 0.0.0.0]

Commands:
  new           command to create a new inventory
```

### Javascript

- [sortable](https://github.com/HubSpot/sortable) for table sorting