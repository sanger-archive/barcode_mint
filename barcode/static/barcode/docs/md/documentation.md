## Registering a barcode
To register a barcode, send a HTTP POST request to `/api/register/`. This request should contain the following json object:
	
	{
		"source": "mylims",
		("barcode": "MYLIMS12345",)
		("uuid": "de305d54-75b4-431b-adb2-eb6b9e546014",)
	}
	
A list of valid LIMS names can be found at `/api/sources/`.

The barcode and uuid fields are optional. If they are not given they will be generated for you. It is recommended that you leave them blank unless there is a reason you need a particular barcode e.g. A barcode from an external source.

This will register the barcode for you and return the following json object:

	{
		"source": "mylims",
		"barcode": "MYLIMS12345",
		"uuid": "de305d54-75b4-431b-adb2-eb6b9e546014",
	}
	
First, you should check the status code. If this is 201 then your barcode has been registered and is guaranteed to be unique. If it is anything else (400, 422), then your barcode has not been registered and the return json will look something like this:

	{
		"errors": [
			{
				"error": "barcode already taken",
				"barcode": "MYLIMS12345"
			},
			{
				"error": "invalid source",
				"source": "mylims"
			}
		]
	}


Possible errors include:

	"malformed barcode"
	"barcode already taken"
	"source missing"
	"invalid source"
	"uuid already taken"
	"malformed uuid"
	
## Registering multiple barcodes
To register multiple barcodes at once send a POST request to `/api/register/batch`. The request body should be a json object like this:

	{
		"source": "mylims",
		"count": 10,
		("barcodes": ["barcode1", "barcode2" ... ],)
		("uuids": ["uuid1", "uuid2" ... ],)
	}
	
The `barcodes` and `uuids`	lists are optional, but if supplied the length of the lists must be equal to `count`.

This will return a json list with an element for each barcode

	[
		{
			"barcode": "BARCODE1",
			"uuid": "54b25c77-abc3-44a5-800b-059aca50bb99",
			"source": "mylims"
		},
		{
			"barcode": "BARCODE2",
			"uuid": "1bac5d19-09b6-4454-829e-7745db6f5929",
			"source": "mylims"
		},
		...
	]
	
If there is an error, none of the barcocdes will be registered and the return json will look like this:

	{
		"errors": [
			{
				"error": "malformed barcodes",
				"barcodes": ["BAR*1", "BAR*2"]
			},
			{
				"error": "uuids already taken",
				"uuids": ["54b25c77-abc3-44a5-800b-059aca50bb99", "1bac5d19-09b6-4454-829e-7745db6f5929"]
			}
		]
	}
	
Possible errors include:

	{
		"error": "wrong number of barcodes given"
	},
	{
		"error": "malformed barcodes",
		"barcodes": [...]
	},
	{
		"error": "barcodes already taken",
		"barcodes": [...]
	},
	{
		"error": "duplicate barcodes given",
		"barcodes": [...]
	},
	{
		"error": "source missing"
	},
	{
		"error": "invalid source",
		"source": ...
	},
	{
		"error": "wrong number of uuids given"
	},
	{
		"error": "uuids already taken",
		"uuids": [...]
	},
	{
		"error": "malformed uuids",
		"uuids": [...]
	},
	{
		"error": "duplicate uuids given",
		"uuids": [...]
	}
	
## Viewing a barcode
To view a information about a barcode sent a HTTP GET request to `/api/barcodes/{barcode}/` with the barcode. This will return a json objects of the barcode supplied or 404.

The json object will look like:
	
	{
		"barcode": "CGAP62",
		"uuid": "9de2c925-f2ca-4ce5-8444-217a6a46db60",
		"source": "cgap",
	}
	
## Searching for barcodes
To view all barcodes send a HTTP GET request to `/api/barcodes/`. You can optionally limit the search to specific critera by using the query parameters `barcode`, `uuid`, `source`, `offset`, and `length`. `offset` specifies where to start displaying barcodes from (default 0) and `length` specifies the number of barcodes to display (default 100).

This will return a list of json objects like this:

	{
	    "count": 150,
	    "next": "http://127.0.0.1:8000/v1/api/barcodes/?limit=100&offset=100&source=cgap",
	    "previous": null,
	    "results": [
			{
				"barcode": "CGAP62",
				"uuid": "9de2c925-f2ca-4ce5-8444-217a6a46db60",
				"source": "cgap",
			},
			{
				"barcode": "CGAP63",
				"uuid": "54b25c77-abc3-44a5-800b-059aca50bb99",
				"source": "cgap",
			},
			...
		]
	}
	
`count` is the total number of barcodes that match the search criteria.	
		
	
## Listing sources
To list the sources send a HTTP GET request to `/api/sources/`. This will return a list of valid sources.

Example json object:

	[
		{
			"name": "cgap"
		},
		{
			"name": "mylims"
		},
		{
			"name": "sscape"
		}
	]