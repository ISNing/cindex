# Cindex

Cindex - A plug-in api framework include OAuth2.0 and Permission control system based on PyCasbin

## What works:

|Name|PackageName|Remarks|
|----|----|----|
|Permission Control based on PyCasbin|`casbin.route`||
|OAuth 2.0 for resource protection|`oauth.route`||
|Cloud Drive Api(Only Onedrive supported yet)|`cloud_drive.restful`||
|YellowPage Data Api for exTHmUI|`exthmui.yellowpage.restful`|Write operation are in protected by casbin and OAuth|
|Updater Api for exTHmUI|`exthmui.updater.restful`|Write operation are in protected by casbin and OAuth|

## How to use

### ! Important: This project is expected to run on python3

1. Get a server with Python3 environment ready  
   (You can also use your own virtual env or something else)
2. Clone this project
3. Open your terminal and come into this folder
4. Run `pip3 install -r requirements.txt` in your shell to make requirements ready
5. Run `python3 manage.py runserver` to init configuration file
6. Modify `conf.json` in this folder as [Configuration](#Configuration)
7. Run `python3 manage.py runserver` again to init plugins' own configuration
8. Modify them too as you want
9. Run `python3 manage.py first_run` to init some pre-configured data, and the password of the pre-configured
   highest-permission user `root` with uid `0` will show up in your terminal now
10. Configure this as a common flask app
11. Everything up-to-date!

## Configuration

Configuration file was placed at the root folder as for `conf.json`  
It expected to be automatically generated after first running the server:`  
For the first startup, you have to fill in some blanks

For `global` items:

|Item|Type|Description|Remarks
|----|----|----|----|
|`url_host`|String|The server's base url.A value used for some operation that needed to redirect to the server from other apis|
|`blu_imports`|String Array|Package name of plugins what is expected to be imported|
|`work_dir`|String|Just like its name, this is the working path of the server|"The current path" for this value is `./`|
|`flask_config`|/(Dict)|Configs for flask|
|`database_uri`|String|Database URI for flask_SQLAlchemy(most of plugins used) by default|

## Customized RESTful Api based on `flask_restx`

Every RESTful Api in this project provided its document(examples of data expected/responses, description of parameters)
at:  
`[The api's Endpoint]/docs`(View in your browser)  
Such as `http://{host}/updater/v1.0/docs`  