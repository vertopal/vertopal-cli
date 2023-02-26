# Vertopal-CLI

**Vertopal-CLI** is a small, yet powerful utility for converting 
digital files to a variety of file formats 
using [Vertopal](https://www.vertopal.com) public API.

You can use Vertopal-CLI by either *terminal commands* or 
*importing as Python package*.

## Installing Vertopal-CLI

Vertopal-CLI is available on [PyPI](https://pypi.org/project/vertopal/):

```bash
$ python -m pip install vertopal
```

You can also download the most recent version of Vertopal-CLI binaries for 
**Windows**, **MacOS**, and **Linux** from the 
[releases page](https://github.com/vertopal/vertopal-cli/releases/latest).

## Using Vertopal-CLI

To use Vertopal-CLI you need to [obtain an App-ID and a Security Token](http://www.vertopal.com/en/account/api/app/new).

Converting files using terminal commands are very simple:

```bash
$ vertopal convert document.ipynb --to pdf
```

To view full command-line help, execute `vertopal --help` 
and `vertopal convert --help` in terminal.

### Setting App ID and Security Token

Before executing `vertopal convert` commands in terminal, you need to set 
your obtained App-ID and Security Token in global configuration file:

```bash
$ vertopal config --app "your-app-id" --token "your-security-token"
```

### Importing as Python package

Importing vertopal as a Python package gives you 
more control and flexibility over each individual task:

```python
>>> import vertopal
>>> response = vertopal.API.upload(
...     filename="document.pdf",
...     filepath="/home/vertopal/document.ipynb",
...     app="your-app-id",
...     token="your-security-token",
... )
>>> response
<Response [200]>
>>> json_response = response.json()
>>> json_response["result"]["output"]["connector"]
'the-connector-of-the-upload-task'
```
