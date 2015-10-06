## Registering barcodes
To register barcodes send a POST request to `/api/barcodes/`. The request body should be a list of barcode objects for a single barcode object.

e.g:

	{
		"source": "mylims",
		"body": "plate"
	}

or

	[
		{
		"source": "mylims",
		"body": "plate"
		},
		{
			"source": "mylims",
			"body": "tube"
		},
		...
	]
	
A barcode object should look like this:
	
	{
		"source": "mylims",
		"body": "plate",
		"barcode": "2000333944",
		"uuid": "4c6717f9-e84d-4209-bb97-e3d7aa9cc856",
		"count": 4
	}

with the following constraints:
* `source` is required, the rest are optional.
* If `count` is supplied neither `barcode` nor `uuid` can be.
* Only `body` or `barcode` can be supplied. Not both.
* `barcode` must be 5 characters or longer.
* `barcode` and `body` can only have letters, numbers, and the symbols `-`, `_`, `:`

The suggested method is to supply `body`. This will generate a barcode in the following format, `SOURCE:BODY:NUMBER` where `SOURCE` and `BODY` are supplied and `NUMBER` is a set of digits to ensure the barcode is unique.
If `body` is not supplied it will be left blank. e.g: `CGAP::42`

If `barcode` is supplied it will attempt to store that specific barcode, but may fail if the barcode is already taken.

This will return a json list with an element for each barcode

	{
		"results": [
			{
				"barcode": "MYLIMS:PLATE:0",
				"uuid": "4c6717f9-e84d-4209-bb97-e3d7aa9cc856",
				"source": "mylims"
			},
			{
				"barcode": "MYLIMS:PLATE:1",
				"uuid": "1aec609a-1338-47d6-bb22-ecb95e2d16e2",
				"source": "mylims"
			}
			...
		]
	}
	
###Example requests:

	{
		"source": "mylims",
		"body": "plate",
		"count": 5
	}
` `

	[
		{
			"source": "gclp",
			"barocde": "1220000000123"
		},
		{
			"source": "gclp",
			"barocde": "1220000000125"
		}
	]
	
If there is an error, none of the barcodes will be registered and the return json will look like this:
	
	{
		"errors": [
			{
				"error": "malformed barcodes",
				"barcodes": [
					"BAR*1",
					"BAR*2"
				]
			},
			{
				"error": "uuids already taken",
				"uuids": [
					"146d410e-b456-4a22-9293-836d897cbcd8",
					"0bd9a1a5-93f8-4d8a-9dba-575e41720681"
				]
			}
		]
	}
	
Possible errors include:

	{
		"error": "invalid sources",
		"sources": [...]
	},
	
	{
		"error": "missing sources",
		"indices": [...]
	},
	{
		"error": "malformed bodies",
		"bodies": [...]
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
		"error": "body and barcode given",
		"indices": [...]
	},
	{
		"error": "malformed uuids",
		"uuids": [...]
	},
	{
		"error": "duplicate uuids given",
		"uuids": [...]
	},
	{
		"error": "uuids already taken",
		"uuids": [...]
	},
	{
		"error": "count and barcode or uuid given",
		"indices": [...]
	}
	
## Viewing a barcode
To view a information about a barcode sent a HTTP GET request to `/api/barcodes/{barcode}/` with the barcode. This will return a json objects of the barcode supplied or 404.

The json object will look like:
	
	{
		"barcode": "CGAP:SARA:62",
		"uuid": "9de2c925-f2ca-4ce5-8444-217a6a46db60",
		"source": "cgap",
	}
	
## Searching for barcodes
To view all barcodes send a HTTP GET request to `/api/barcodes/`. You can optionally limit the search to specific critera by using the query parameters `barcode`, `uuid`, `source`, `offset`, and `length`. 

`barcode`, `uuid` or `source` can either be a single element or a comma separated list.

`offset` specifies where to start displaying barcodes from (default 0) and `length` specifies the number of barcodes to display (default 100).

This will return a list of json objects like this:

	{
	    "count": 150,
	    "next": "http://127.0.0.1:8000/v1/api/barcodes/?limit=100&offset=100&source=cgap",
	    "previous": null,
	    "results": [
			{
				"barcode": "CGAP:SARA:62",
				"uuid": "9de2c925-f2ca-4ce5-8444-217a6a46db60",
				"source": "cgap",
			},
			{
				"barcode": "CGAP:SARA:63",
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
