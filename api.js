const easyEDAApi = [
    {
        "name": "getSource",
        "description": "Get the source of the current EasyEDA document.",
        "parameters": [
            { "name": "type", "type": "string", "description": "The format of the source to retrieve. Can be 'json', 'compress', or 'svg'." }
        ],
        "example": "var result = api('getSource', {type:'json'});"
    },
    {
        "name": "applySource",
        "description": "Apply a source to the EasyEDA editor.",
        "parameters": [
            { "name": "source", "type": "string or object", "description": "The source to apply. Can be a compress string or a JSON object." },
            { "name": "createNew", "type": "boolean", "description": "If true, a new editor will be opened." }
        ],
        "example": "api('applySource', {source: json, createNew: !true});"
    },
    {
        "name": "getShape",
        "description": "Get an EasyEDA JSON object by its ID.",
        "parameters": [
            { "name": "id", "type": "string", "description": "The ID of the shape to retrieve." }
        ],
        "example": "var obj = api('getShape', {id:'gge13'});"
    },
    {
        "name": "deleteShapes",
        "description": "Remove shapes from the document.",
        "parameters": [
             { "name": "ids", "type": "array", "description": "An array of shape IDs to delete." }
        ],
        "example": "api('delete', {ids:[\"gge2\",\"gge3\"]});"
    },
    {
        "name": "updateShape",
        "description": "Modify an EasyEDA object.",
        "parameters": [
            { "name": "shapeType", "type": "string", "description": "The type of the shape to update." },
            { "name": "gId", "type": "string", "description": "The ID of the shape to update." },
            { "name": "jsonCache", "type": "object", "description": "An object containing the properties to update." }
        ],
        "example": "api('updateShape', { \"shapeType\": \"PAD\", \"jsonCache\": { \"gId\": \"gge5\", \"net\": \"GND\", \"shape\": \"ELLIPSE\" }});"
    },
    {
        "name": "createShape",
        "description": "Create a new shape in the document.",
        "parameters": [
            { "name": "shapeType", "type": "string", "description": "The type of shape to create." },
            { "name": "jsonCache", "type": "object", "description": "An object containing the properties of the new shape." }
        ],
        "example": "api('createShape', {\n  \"shapeType\": \"PAD\",\n  \"jsonCache\": {\n    \"gId\": \"gge5\",\n    \"layerid\": \"11\",\n    \"shape\": \"ELLIPSE\",\n    \"x\": 382,\n    \"y\": 208,\n    \"net\": \"\",\n    \"width\": 6,\n    \"height\": 6,\n    \"number\": \"1\",\n    \"holeR\": 1.8,\n    \"pointArr\": [],\n    \"rotation\": \"0\"\n  }\n});"
    },
    {
        "name": "createToolbarButton",
        "description": "Create a button on the toolbar.",
        "parameters": [
            { "name": "icon", "type": "string", "description": "Path to the button icon." },
            { "name": "title", "type": "string", "description": "Tooltip for the button." },
            { "name": "fordoctype", "type": "string", "description": "Comma-separated list of document types where the button should appear (e.g., 'sch,schlib')." },
            { "name": "cmd", "type": "string", "description": "Command to execute when the button is clicked." }
        ],
        "example": "api('createToolbarButton', {\n  icon:'extensions/theme/icon.svg',\n  title:'Theme Colors...',\n  fordoctype:'sch,schlib',\n  cmd:\"extension-theme-setting\"\n});"
    }
];