## Registering barcodes
To register barcodes send a POST request to `/api/barcodes/`. The request body should be a json object like this:

	{
		"source": "mylims",
		("count": 10,)
		("barcode": "barcode1",)
		("uuid": "uuid1",)
	}

or

	[
		{
			"source": "mylims",
			("count": 10,)
			("barcode": "barcode1",)
			("uuid": "uuid1",)
		},
		{
			"source": "mylims",
			("count": 10,)
			("barcode": "barcode2",)
			("uuid": "uuid2",)
		},
		...
	]
	
`count`, `barcodes`, and `uuids`	are optional. But if `count` is supplied neither `barcode` nor `uuid` can be.

For each element in the list, if `count` is supplied it will generate that many barcodes with the source supplied.
If `barcode` and/or `uuid` is supplied it will generate a barcode with that `source`, `barcode`, and `uuid`.

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
		"error": "sources missing",
		"indices": [...]
	},
	{
		"error": "invalid sources",
		"sources": [...]
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
	},
	{
		"error": "cannot have both count and barcode or uuid",
		"indices": [...]
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