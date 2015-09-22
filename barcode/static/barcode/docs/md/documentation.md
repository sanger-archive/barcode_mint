## Registering a barcode
To register a barcode, send a HTTP POST request to `/api/register/`. This request should contain the following json object:
	
	{
		"source" = "myLims",
		["barcode" = "MYLIMS12345",]
		["uuid" = "de305d54-75b4-431b-adb2-eb6b9e546014",]
	}
	
A list of valid LIMS names can be found at `/api/source/list/`.

The barcode and uuid fields are optional. If they are not given they will be generated for you. It is recommended that you leave them blank unless there is a reason you need a particular barcode e.g. A barcode from an external source.

This will register the barcode for you and return the following json object:

	{
		"source": "myLims",
		"barcode": "MYLIMS12345",
		"uuid": "de305d54-75b4-431b-adb2-eb6b9e546014",
		"errors": ["error1", "error2"],
	}
	
First, you should check the status code. If this is 201 then your barcode has been registered and is guaranteed to be unique. If it is anything else (400, 422), then your barcode has not been registered and you should check `errors` to determine what went wrong. Possible errors include:

	"barcode too short"
	"malformed barcode"
	"barcode already taken"
	"source missing"
	"invalid source"
	"uuid already taken"
	"malformed uuid"
	
## Viewing a barcode
To view a information about a barcode sent a HTTP GET request to `/api/barcode/{barcode}/` with the barcode or `/api/uuid/{uuid}/` with the UUID. This will return a json object about the barcode supplied or 404.

The json object will look like:
	
	{
		"barcode": "CGAP62",
		"uuid": "9de2c925-f2ca-4ce5-8444-217a6a46db60",
		"source": "cgap",
	}
	
## Listing sources
To list the sources send a HTTP GET request to `api/source/list/`. This will return a list of valid sources.

Example json object:

	{
		"sources": [
			"mylims",
			"sscape",
			"cgap",
		]
	}	